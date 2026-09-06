package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class PaymentResponse {

    public static class Initiate {
        @SerializedName("pidx")
        private String pidx;
        
        @SerializedName("payment_url")
        private String paymentUrl;

        @SerializedName("form_url")
        private String formUrl;

        @SerializedName("post_data")
        private String postData;

        @SerializedName("form_html")
        private String formHtml;

        public String getPidx() { return pidx; }
        public void setPidx(String pidx) { this.pidx = pidx; }

        public String getPaymentUrl() { return paymentUrl; }
        public void setPaymentUrl(String paymentUrl) { this.paymentUrl = paymentUrl; }

        public String getFormUrl() { return formUrl; }
        public void setFormUrl(String formUrl) { this.formUrl = formUrl; }

        public String getPostData() { return postData; }
        public void setPostData(String postData) { this.postData = postData; }

        public String getFormHtml() { return formHtml; }
        public void setFormHtml(String formHtml) { this.formHtml = formHtml; }
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
