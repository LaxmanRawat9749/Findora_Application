package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class PaymentRequest {

    public static class Initiate {
        @SerializedName("item_id")
        private int itemId;
        
        @SerializedName("package")
        private String pkg;

        public Initiate(int itemId, String pkg) {
            this.itemId = itemId;
            this.pkg = pkg;
        }

        public int getItemId() { return itemId; }
        public void setItemId(int itemId) { this.itemId = itemId; }

        public String getPkg() { return pkg; }
        public void setPkg(String pkg) { this.pkg = pkg; }
    }

    public static class Verify {
        @SerializedName("payment_id")
        private int paymentId;
        
        @SerializedName("token")
        private String token;

        public Verify(int paymentId, String token) {
            this.paymentId = paymentId;
            this.token = token;
        }

        public int getPaymentId() { return paymentId; }
        public void setPaymentId(int paymentId) { this.paymentId = paymentId; }

        public String getToken() { return token; }
        public void setToken(String token) { this.token = token; }
    }
}
