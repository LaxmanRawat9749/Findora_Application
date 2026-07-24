package com.findora.app.network;

import com.findora.app.models.*;
import java.util.List;
import retrofit2.Call;
import retrofit2.http.*;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;

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

    // ─── Profile ─────────────────────────────────────────────
    @GET("profile/")
    Call<User> getProfile();

    @PUT("profile/")
    Call<User> updateProfile(@Body User user);

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
    Call<Item> reportItemWithImage(
        @Part("type") RequestBody type,
        @Part("title") RequestBody title,
        @Part("description") RequestBody description,
        @Part("category") RequestBody category,
        @Part("location") RequestBody location,
        @Part("reward") RequestBody reward,
        @Part MultipartBody.Part image
    );

    @POST("items/")
    Call<Item> reportItem(@Body Item item);

    @PUT("items/{id}/")
    Call<Item> updateItem(@Path("id") int id, @Body Item item);

    @DELETE("items/{id}/")
    Call<MessageResponse> deleteItem(@Path("id") int id);

    // ─── Admin ───────────────────────────────────────────────
    @GET("admin/items/")
    Call<List<Item>> getPendingItems();

    @POST("admin/items/{id}/verify/")
    Call<MessageResponse> verifyItem(@Path("id") int id, @Body AdminAction action);

    // ─── Claims ──────────────────────────────────────────────
    @POST("claims/")
    Call<Claim> submitClaim(@Body Claim claim);

    // ─── Chat ────────────────────────────────────────────────
    @GET("chat/")
    Call<List<ChatMessage>> getMessages(@Query("item_id") int itemId);

    @POST("chat/")
    Call<ChatMessage> sendMessage(@Body ChatMessage message);

    // ─── Notifications ───────────────────────────────────────
    @GET("notifications/")
    Call<List<Notification>> getNotifications();

    @POST("notifications/{id}/read/")
    Call<MessageResponse> markNotificationRead(@Path("id") int id);
}
