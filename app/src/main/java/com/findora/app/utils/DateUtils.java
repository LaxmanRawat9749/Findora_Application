package com.findora.app.utils;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

public class DateUtils {
    
    // Nepal timezone
    private static final String TARGET_TIMEZONE = "Asia/Kathmandu";

    /**
     * Parse an ISO-8601 UTC string (e.g. 2026-07-28T04:21:00Z) to a Date object.
     */
    public static Date parseUtcString(String utcString) {
        if (utcString == null || utcString.trim().isEmpty()) return null;
        try {
            SimpleDateFormat format;
            if (utcString.contains(".")) {
                format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US);
            } else {
                format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US);
            }
            format.setTimeZone(TimeZone.getTimeZone("UTC"));
            return format.parse(utcString);
        } catch (ParseException e) {
            // Fallback for missing 'Z' or non-standard formats
            try {
                SimpleDateFormat fallback = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US);
                fallback.setTimeZone(TimeZone.getTimeZone("UTC"));
                return fallback.parse(utcString);
            } catch (ParseException e2) {
                return null;
            }
        }
    }

    /**
     * Format a UTC string to localized chat time (e.g., 10:06 AM).
     */
    public static String formatChatTime(String utcString) {
        Date date = parseUtcString(utcString);
        if (date == null) {
            // Fallback behavior
            if (utcString != null && utcString.contains("T")) {
                String timePart = utcString.split("T")[1];
                return timePart.substring(0, Math.min(5, timePart.length()));
            }
            return utcString != null ? utcString : "";
        }
        SimpleDateFormat outFormat = new SimpleDateFormat("hh:mm a", Locale.US);
        outFormat.setTimeZone(TimeZone.getTimeZone(TARGET_TIMEZONE));
        return outFormat.format(date);
    }

    /**
     * Format a UTC string to localized conversation time (e.g., Jul 28, 10:06 AM).
     */
    public static String formatConversationTime(String utcString) {
        Date date = parseUtcString(utcString);
        if (date == null) {
            return utcString != null ? utcString : "";
        }
        SimpleDateFormat outFormat = new SimpleDateFormat("MMM dd, hh:mm a", Locale.US);
        outFormat.setTimeZone(TimeZone.getTimeZone(TARGET_TIMEZONE));
        return outFormat.format(date);
    }
    
    /**
     * Format a UTC string to localized notification time (e.g., Jul 28, 2026).
     */
    public static String formatNotificationTime(String utcString) {
        Date date = parseUtcString(utcString);
        if (date == null) {
            if (utcString != null && utcString.contains("T")) {
                return utcString.split("T")[0];
            }
            return utcString != null ? utcString : "";
        }
        SimpleDateFormat outFormat = new SimpleDateFormat("MMM dd, yyyy", Locale.US);
        outFormat.setTimeZone(TimeZone.getTimeZone(TARGET_TIMEZONE));
        return outFormat.format(date);
    }
}
