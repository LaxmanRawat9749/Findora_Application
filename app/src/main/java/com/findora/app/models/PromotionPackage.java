package com.findora.app.models;

public class PromotionPackage {
    private String id;
    private String durationText;
    private double price;

    public PromotionPackage(String id, String durationText, double price) {
        this.id = id;
        this.durationText = durationText;
        this.price = price;
    }

    public String getId() {
        return id;
    }

    public String getDurationText() {
        return durationText;
    }

    public double getPrice() {
        return price;
    }
}
