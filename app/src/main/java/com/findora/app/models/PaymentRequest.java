package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class PaymentRequest {

    public static class Initiate {
        @SerializedName("item_id")
        private int itemId;
        
        @SerializedName("package")
        private String packageKey;
        
        @SerializedName("provider")
        private String provider;

        public Initiate(int itemId, String packageKey, String provider) {
            this.itemId = itemId;
            this.packageKey = packageKey;
            this.provider = provider;
        }

        public int getItemId() { return itemId; }
        public void setItemId(int itemId) { this.itemId = itemId; }

        public String getPackageKey() { return packageKey; }
        public String getProvider() { return provider; }
    }

    public static class Verify {
        @SerializedName("pidx")
        private String pidx;

        public Verify(String pidx) {
            this.pidx = pidx;
        }

        public String getPidx() { return pidx; }
        public void setPidx(String pidx) { this.pidx = pidx; }
    }
}
