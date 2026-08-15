package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class PaymentResponse {

    public static class Initiate {
        @SerializedName("payment_id")
        private int paymentId;
        
        private double amount;
        
        @SerializedName("amount_paisa")
        private long amountPaisa;
        
        @SerializedName("public_key")
        private String publicKey;
        
        @SerializedName("product_identity")
        private String productIdentity;
        
        @SerializedName("product_name")
        private String productName;

        public int getPaymentId() { return paymentId; }
        public void setPaymentId(int paymentId) { this.paymentId = paymentId; }

        public double getAmount() { return amount; }
        public void setAmount(double amount) { this.amount = amount; }

        public long getAmountPaisa() { return amountPaisa; }
        public void setAmountPaisa(long amountPaisa) { this.amountPaisa = amountPaisa; }

        public String getPublicKey() { return publicKey; }
        public void setPublicKey(String publicKey) { this.publicKey = publicKey; }

        public String getProductIdentity() { return productIdentity; }
        public void setProductIdentity(String productIdentity) { this.productIdentity = productIdentity; }

        public String getProductName() { return productName; }
        public void setProductName(String productName) { this.productName = productName; }
    }

    public static class Verify {
        private boolean success;
        
        private String message;
        
        @SerializedName("featured_until")
        private String featuredUntil;

        public boolean isSuccess() { return success; }
        public void setSuccess(boolean success) { this.success = success; }

        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }

        public String getFeaturedUntil() { return featuredUntil; }
        public void setFeaturedUntil(String featuredUntil) { this.featuredUntil = featuredUntil; }
    }
}
