package com.findora.app.network;

import com.findora.app.models.*;
import java.util.List;
import retrofit2.Call;
import retrofit2.http.*;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import java.util.Map;

public interface ApiService {

    // ─── Auth ────────────────────────────────────────────────
    @POST("register/")
    Call<MessageResponse> register(@Body RegisterRequest request);

    @POST("verify-otp/")
    Call<MessageResponse> verifyOtp(@Body OtpRequest request);

    @POST("resend-otp/")
    Call<MessageResponse> resendOtp(@Body OtpRequest request);

    @POST("login/")
    Call<AuthResponse> login(@Body LoginRequest request);

    @POST("logout/")
    Call<MessageResponse> logout(@Body RefreshRequest request);

    @POST("token/refresh/")
    Call<TokenResponse> refreshToken(@Body RefreshRequest request);

    @POST("forgot-password/")
    Call<MessageResponse> forgotPassword(@Body EmailRequest request);

    @POST("reset-password/")
    Call<MessageResponse> resetPassword(@Body ResetPasswordRequest request);

    @POST("change-password/")
    Call<MessageResponse> changePassword(@Body ChangePasswordRequest request);

    @POST("change-username/")
    Call<ChangeUsernameResponse> changeUsername(@Body ChangeUsernameRequest request);

    // ─── Profile ─────────────────────────────────────────────
    @GET("profile/")
    Call<User> getProfile();

    @PUT("profile/")
    Call<User> updateProfile(@Body User user);

    @Multipart
    @PUT("profile/image/")
    Call<User> updateProfileImage(@Part MultipartBody.Part profileImage);

    @DELETE("profile/image/")
    Call<User> deleteProfileImage();

    @GET("users/{id}/public-profile/")
    Call<PublicProfile> getPublicProfile(@Path("id") int userId);

    @GET("profile/items/")
    Call<List<Item>> getMyReports();

    // ─── Items ───────────────────────────────────────────────
    @GET("items/")
    Call<List<Item>> getItems();

    @GET("items/")
    Call<List<Item>> searchItems(@Query("search") String query);

    @GET("items/")
    Call<List<Item>> filterByType(@Query("type") String type);

    @GET("items/")
    Call<List<Item>> filterByCategory(@Query("category") String category);

    @GET("items/")
    Call<List<Item>> getItemsWithFilter(
        @Query("search") String search,
        @Query("type") String type,
        @Query("category") String category
    );

    @GET("items/{id}/")
    Call<Item> getItemDetail(@Path("id") int id);

    @Multipart
    @POST("items/")
    Call<Item> reportItemWithImages(
            @PartMap Map<String, RequestBody> partMap,
            @Part List<MultipartBody.Part> images
    );

    @PUT("items/{id}/")
    Call<Item> updateItem(@Path("id") int id, @Body Item item);

    @DELETE("items/{id}/")
    Call<MessageResponse> deleteItem(@Path("id") int id);

    @POST("items/{id}/mark-returned/")
    Call<MessageResponse> markItemReturned(@Path("id") int id);

    @POST("items/{id}/confirm-return/")
    Call<MessageResponse> confirmItemReturn(@Path("id") int id);

    // ─── Admin ───────────────────────────────────────────────
    @GET("admin/items/")
    Call<List<Item>> getPendingItems();

    @POST("admin/items/{id}/verify/")
    Call<MessageResponse> verifyItem(@Path("id") int id, @Body AdminAction action);


    // ─── Conversations ───────────────────────────────────────
    @GET("conversations/")
    Call<List<Conversation>> getConversations();

    @POST("conversations/init/")
    Call<ConversationInitResponse> initConversation(@Body ConversationInitRequest request);

    // ─── Chat ────────────────────────────────────────────────
    @GET("chat/")
    Call<List<ChatMessage>> getMessages(@Query("conversation_id") int conversationId);

    @POST("chat/")
    Call<ChatMessage> sendMessage(@Body ChatMessage message);

    @Multipart
    @POST("chat/")
    Call<ChatMessage> sendImageMessage(
        @Part("conversation") RequestBody conversation,
        @Part("message_type") RequestBody messageType,
        @Part("caption") RequestBody caption,
        @Part MultipartBody.Part image
    );

    @GET("chat/profile/")
    Call<User> getChatProfile(@Query("conversation_id") int conversationId);

    @PUT("chat/message/{id}/")
    Call<ChatMessage> editMessage(@Path("id") int id, @Body ChatMessage message);

    @DELETE("chat/message/{id}/")
    Call<MessageResponse> deleteMessage(@Path("id") int id, @Query("for_everyone") boolean forEveryone);

    @DELETE("chat/conversation/{id}/")
    Call<MessageResponse> removeConversation(@Path("id") int id);

    // ─── Notifications ───────────────────────────────────────
    @GET("notifications/")
    Call<List<Notification>> getNotifications();

    @POST("notifications/{id}/read/")
    Call<MessageResponse> markNotificationRead(@Path("id") int id);
}
