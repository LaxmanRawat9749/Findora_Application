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
        @SerializedName("pidx")
        private String pidx;

        public Verify(String pidx) {
            this.pidx = pidx;
        }

        public String getPidx() { return pidx; }
        public void setPidx(String pidx) { this.pidx = pidx; }
    }
}
