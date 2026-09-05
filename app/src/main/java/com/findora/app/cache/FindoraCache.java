package com.findora.app.cache;

import android.content.Context;
import android.util.Log;

import com.findora.app.models.ChatMessage;
import com.findora.app.models.Conversation;
import com.findora.app.models.Item;
import com.findora.app.models.PublicProfile;
import com.findora.app.models.User;
import com.findora.app.utils.SessionManager;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * High-performance, thread-safe central cache for Findora.
 *
 * Implements a 2-tier caching strategy:
 *  - L1: Fast In-Memory Map (0ms read time).
 *  - L2: Persistent Disk Storage (survives app kill/restarts, works offline).
 *
 * All user-specific data is partitioned by User ID to enforce strict user isolation.
 */
public class FindoraCache {

    private static final String TAG = "FindoraCache";
    private static final String CACHE_DIR_NAME = "findora_cache";

    private static volatile FindoraCache instance;
    private final Context context;
    private final Gson gson;
    private final File cacheDir;

    // L1 In-Memory Caches
    private final Map<String, Object> memoryCache = new ConcurrentHashMap<>();

    private FindoraCache(Context context) {
        this.context = context.getApplicationContext();
        this.gson = new Gson();
        this.cacheDir = new File(this.context.getFilesDir(), CACHE_DIR_NAME);
        if (!cacheDir.exists()) {
            //noinspection ResultOfMethodCallIgnored
            cacheDir.mkdirs();
        }
    }

    public static FindoraCache getInstance(Context context) {
        if (instance == null) {
            synchronized (FindoraCache.class) {
                if (instance == null) {
                    instance = new FindoraCache(context);
                }
            }
        }
        return instance;
    }

    private int getCurrentUserId() {
        return new SessionManager(context).getUserId();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // 1. ITEM CACHE (Feeds, Detail, Updates, Deletions)
    // ─────────────────────────────────────────────────────────────────────────

    public void saveItems(List<Item> items) {
        if (items == null) return;
        int userId = getCurrentUserId();
        String key = "items_feed_" + userId;
        memoryCache.put(key, new ArrayList<>(items));
        writeToDisk(key + ".json", items);

        // Also update individual item detail caches
        for (Item item : items) {
            if (item != null && item.getId() > 0) {
                saveItemDetail(item, false);
            }
        }
    }

    public List<Item> getCachedItems() {
        int userId = getCurrentUserId();
        String key = "items_feed_" + userId;

        // Try L1 Memory
        Object inMemory = memoryCache.get(key);
        if (inMemory instanceof List) {
            //noinspection unchecked
            return (List<Item>) inMemory;
        }

        // Try L2 Disk
        Type type = new TypeToken<List<Item>>() {}.getType();
        List<Item> diskItems = readFromDisk(key + ".json", type);
        if (diskItems != null) {
            memoryCache.put(key, diskItems);
            return diskItems;
        }

        return Collections.emptyList();
    }

    public void saveItemDetail(Item item) {
        saveItemDetail(item, true);
    }

    private void saveItemDetail(Item item, boolean updateFeed) {
        if (item == null || item.getId() <= 0) return;
        String key = "item_detail_" + item.getId();
        memoryCache.put(key, item);
        writeToDisk(key + ".json", item);

        if (updateFeed) {
            updateOrInsertItem(item);
        }
    }

    public Item getCachedItemDetail(int itemId) {
        if (itemId <= 0) return null;
        String key = "item_detail_" + itemId;

        Object inMemory = memoryCache.get(key);
        if (inMemory instanceof Item) {
            return (Item) inMemory;
        }

        Item diskItem = readFromDisk(key + ".json", Item.class);
        if (diskItem != null) {
            memoryCache.put(key, diskItem);
            return diskItem;
        }

        // Fallback: search in cached feed list
        List<Item> cachedItems = getCachedItems();
        for (Item it : cachedItems) {
            if (it != null && it.getId() == itemId) {
                memoryCache.put(key, it);
                return it;
            }
        }
        return null;
    }

    public void updateOrInsertItem(Item item) {
        if (item == null || item.getId() <= 0) return;
        List<Item> currentItems = new ArrayList<>(getCachedItems());
        boolean found = false;
        for (int i = 0; i < currentItems.size(); i++) {
            if (currentItems.get(i) != null && currentItems.get(i).getId() == item.getId()) {
                currentItems.set(i, item);
                found = true;
                break;
            }
        }
        if (!found) {
            currentItems.add(0, item);
        }
        saveItems(currentItems);
    }

    public void removeItem(int itemId) {
        if (itemId <= 0) return;
        String detailKey = "item_detail_" + itemId;
        memoryCache.remove(detailKey);
        deleteDiskFile(detailKey + ".json");

        List<Item> currentItems = new ArrayList<>(getCachedItems());
        boolean modified = false;
        for (int i = 0; i < currentItems.size(); i++) {
            if (currentItems.get(i) != null && currentItems.get(i).getId() == itemId) {
                currentItems.remove(i);
                modified = true;
                break;
            }
        }
        if (modified) {
            saveItems(currentItems);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // 2. PROFILE CACHE (User profile & Public Profiles)
    // ─────────────────────────────────────────────────────────────────────────

    public void saveUserProfile(User user) {
        if (user == null) return;
        int userId = user.getId() > 0 ? user.getId() : getCurrentUserId();
        String key = "profile_" + userId;
        memoryCache.put(key, user);
        writeToDisk(key + ".json", user);
    }

    public User getCachedUserProfile() {
        int userId = getCurrentUserId();
        if (userId <= 0) return null;
        String key = "profile_" + userId;

        Object inMemory = memoryCache.get(key);
        if (inMemory instanceof User) {
            return (User) inMemory;
        }

        User diskUser = readFromDisk(key + ".json", User.class);
        if (diskUser != null) {
            memoryCache.put(key, diskUser);
            return diskUser;
        }
        return null;
    }

    public void savePublicProfile(int targetUserId, PublicProfile profile) {
        if (targetUserId <= 0 || profile == null) return;
        String key = "public_profile_" + targetUserId;
        memoryCache.put(key, profile);
        writeToDisk(key + ".json", profile);
    }

    public PublicProfile getCachedPublicProfile(int targetUserId) {
        if (targetUserId <= 0) return null;
        String key = "public_profile_" + targetUserId;

        Object inMemory = memoryCache.get(key);
        if (inMemory instanceof PublicProfile) {
            return (PublicProfile) inMemory;
        }

        PublicProfile diskProfile = readFromDisk(key + ".json", PublicProfile.class);
        if (diskProfile != null) {
            memoryCache.put(key, diskProfile);
            return diskProfile;
        }
        return null;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // 3. CHAT CACHE (Conversations & Incremental Message History)
    // ─────────────────────────────────────────────────────────────────────────

    public void saveConversations(List<Conversation> conversations) {
        if (conversations == null) return;
        int userId = getCurrentUserId();
        String key = "conversations_" + userId;
        memoryCache.put(key, new ArrayList<>(conversations));
        writeToDisk(key + ".json", conversations);
    }

    public List<Conversation> getCachedConversations() {
        int userId = getCurrentUserId();
        String key = "conversations_" + userId;

        Object inMemory = memoryCache.get(key);
        if (inMemory instanceof List) {
            //noinspection unchecked
            return (List<Conversation>) inMemory;
        }

        Type type = new TypeToken<List<Conversation>>() {}.getType();
        List<Conversation> diskList = readFromDisk(key + ".json", type);
        if (diskList != null) {
            memoryCache.put(key, diskList);
            return diskList;
        }
        return Collections.emptyList();
    }

    public void saveMessages(int conversationId, List<ChatMessage> messages) {
        if (conversationId <= 0 || messages == null) return;
        int userId = getCurrentUserId();
        String key = "chat_messages_" + conversationId + "_" + userId;
        memoryCache.put(key, new ArrayList<>(messages));
        writeToDisk(key + ".json", messages);
    }

    public List<ChatMessage> getCachedMessages(int conversationId) {
        if (conversationId <= 0) return Collections.emptyList();
        int userId = getCurrentUserId();
        String key = "chat_messages_" + conversationId + "_" + userId;

        Object inMemory = memoryCache.get(key);
        if (inMemory instanceof List) {
            //noinspection unchecked
            return (List<ChatMessage>) inMemory;
        }

        Type type = new TypeToken<List<ChatMessage>>() {}.getType();
        List<ChatMessage> diskMessages = readFromDisk(key + ".json", type);
        if (diskMessages != null) {
            memoryCache.put(key, diskMessages);
            return diskMessages;
        }
        return Collections.emptyList();
    }

    /**
     * Appends new incoming messages from incremental sync, avoiding duplicates.
     */
    public List<ChatMessage> appendMessages(int conversationId, List<ChatMessage> newMessages) {
        if (conversationId <= 0) return Collections.emptyList();
        if (newMessages == null || newMessages.isEmpty()) {
            return getCachedMessages(conversationId);
        }

        List<ChatMessage> existing = new ArrayList<>(getCachedMessages(conversationId));
        Map<Integer, ChatMessage> map = new LinkedHashMap<>();

        for (ChatMessage m : existing) {
            if (m != null) {
                map.put(m.getId(), m);
            }
        }
        for (ChatMessage m : newMessages) {
            if (m != null) {
                map.put(m.getId(), m); // Merges or appends newer messages
            }
        }

        List<ChatMessage> merged = new ArrayList<>(map.values());
        saveMessages(conversationId, merged);
        return merged;
    }

    public void addSentMessage(int conversationId, ChatMessage msg) {
        if (conversationId <= 0 || msg == null) return;
        List<ChatMessage> existing = new ArrayList<>(getCachedMessages(conversationId));
        existing.add(msg);
        saveMessages(conversationId, existing);
    }

    public void updateMessage(int conversationId, ChatMessage updatedMsg) {
        if (conversationId <= 0 || updatedMsg == null) return;
        List<ChatMessage> existing = new ArrayList<>(getCachedMessages(conversationId));
        for (int i = 0; i < existing.size(); i++) {
            if (existing.get(i) != null && existing.get(i).getId() == updatedMsg.getId()) {
                existing.set(i, updatedMsg);
                break;
            }
        }
        saveMessages(conversationId, existing);
    }

    public void deleteMessage(int conversationId, int messageId, boolean forEveryone) {
        if (conversationId <= 0 || messageId <= 0) return;
        List<ChatMessage> existing = new ArrayList<>(getCachedMessages(conversationId));
        for (int i = 0; i < existing.size(); i++) {
            ChatMessage msg = existing.get(i);
            if (msg != null && msg.getId() == messageId) {
                msg.setDeletedForEveryone(true);
                if ("image".equals(msg.getMessageType())) {
                    msg.setMessage("This image was deleted");
                    msg.setImageUrl(null);
                    msg.setCaption("");
                } else {
                    msg.setMessage("This message was deleted");
                }
                break;
            }
        }
        saveMessages(conversationId, existing);
    }

    public int getLatestMessageId(int conversationId) {
        List<ChatMessage> messages = getCachedMessages(conversationId);
        if (messages.isEmpty()) return 0;
        int maxId = 0;
        for (ChatMessage m : messages) {
            if (m != null && m.getId() > maxId) {
                maxId = m.getId();
            }
        }
        return maxId;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // 4. USER ISOLATION & CLEANUP
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Clears all private user-specific caches on logout to avoid cross-user data leakage.
     */
    public synchronized void clearUserCache(int userId) {
        if (userId <= 0) return;
        Log.i(TAG, "Wiping private cache partitions for userId=" + userId);

        memoryCache.clear();

        File[] files = cacheDir.listFiles();
        if (files != null) {
            String userSuffix = "_" + userId;
            for (File file : files) {
                String name = file.getName();
                if (name.contains(userSuffix)) {
                    //noinspection ResultOfMethodCallIgnored
                    file.delete();
                }
            }
        }
    }

    public synchronized void clearAll() {
        memoryCache.clear();
        File[] files = cacheDir.listFiles();
        if (files != null) {
            for (File file : files) {
                //noinspection ResultOfMethodCallIgnored
                file.delete();
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // 5. INTERNAL DISK I/O HELPERS
    // ─────────────────────────────────────────────────────────────────────────

    private synchronized void writeToDisk(String filename, Object data) {
        try {
            File targetFile = new File(cacheDir, filename);
            File tempFile = new File(cacheDir, filename + ".tmp");

            try (FileOutputStream fos = new FileOutputStream(tempFile);
                 OutputStreamWriter writer = new OutputStreamWriter(fos, StandardCharsets.UTF_8)) {
                gson.toJson(data, writer);
                writer.flush();
            }

            if (tempFile.exists()) {
                if (targetFile.exists()) {
                    //noinspection ResultOfMethodCallIgnored
                    targetFile.delete();
                }
                //noinspection ResultOfMethodCallIgnored
                tempFile.renameTo(targetFile);
            }
        } catch (Exception e) {
            Log.w(TAG, "Failed writing cache file: " + filename, e);
        }
    }

    private synchronized <T> T readFromDisk(String filename, Type type) {
        File file = new File(cacheDir, filename);
        if (!file.exists() || file.length() == 0) return null;

        try (FileInputStream fis = new FileInputStream(file);
             InputStreamReader reader = new InputStreamReader(fis, StandardCharsets.UTF_8)) {
            return gson.fromJson(reader, type);
        } catch (Exception e) {
            Log.w(TAG, "Failed reading cache file: " + filename, e);
            //noinspection ResultOfMethodCallIgnored
            file.delete();
            return null;
        }
    }

    private synchronized <T> T readFromDisk(String filename, Class<T> clazz) {
        return readFromDisk(filename, (Type) clazz);
    }

    private synchronized void deleteDiskFile(String filename) {
        File file = new File(cacheDir, filename);
        if (file.exists()) {
            //noinspection ResultOfMethodCallIgnored
            file.delete();
        }
    }
}
