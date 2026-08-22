package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class RatingStatusResponse {
    @SerializedName("can_rate")
    private boolean canRate;
    @SerializedName("has_rated")
    private boolean hasRated;
    private FinderRating rating;

    public RatingStatusResponse() {}

    public boolean isCanRate() { return canRate; }
    public void setCanRate(boolean canRate) { this.canRate = canRate; }

    public boolean isHasRated() { return hasRated; }
    public void setHasRated(boolean hasRated) { this.hasRated = hasRated; }

    public FinderRating getRating() { return rating; }
    public void setRating(FinderRating rating) { this.rating = rating; }
}
