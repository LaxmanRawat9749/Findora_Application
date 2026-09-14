package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.models.PotentialMatch;
import com.google.android.material.button.MaterialButton;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class PotentialMatchAdapter extends RecyclerView.Adapter<PotentialMatchAdapter.ViewHolder> {

    public interface OnMatchActionListener {
        void onViewItemClick(int itemId);
        void onVerifyClick(PotentialMatch match);
    }

    private final Context context;
    private final List<PotentialMatch> matches = new ArrayList<>();
    private final int currentUserId;
    private final OnMatchActionListener listener;

    public PotentialMatchAdapter(Context context, int currentUserId, OnMatchActionListener listener) {
        this.context = context;
        this.currentUserId = currentUserId;
        this.listener = listener;
    }

    public void setMatches(List<PotentialMatch> newMatches) {
        matches.clear();
        if (newMatches != null) {
            matches.addAll(newMatches);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(context).inflate(R.layout.item_potential_match, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        PotentialMatch match = matches.get(position);
        holder.bind(match);
    }

    @Override
    public int getItemCount() {
        return matches.size();
    }

    class ViewHolder extends RecyclerView.ViewHolder {
        final TextView tvMatchScore;
        final TextView tvVerificationStatus;
        final ImageView ivItemThumbnail;
        final TextView tvItemTitle;
        final TextView tvTraitsSummary;
        final TextView tvLocationAndTime;
        final TextView tvMatchReasons;
        final MaterialButton btnViewItem;
        final MaterialButton btnStartVerify;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvMatchScore = itemView.findViewById(R.id.tvMatchScore);
            tvVerificationStatus = itemView.findViewById(R.id.tvVerificationStatus);
            ivItemThumbnail = itemView.findViewById(R.id.ivItemThumbnail);
            tvItemTitle = itemView.findViewById(R.id.tvItemTitle);
            tvTraitsSummary = itemView.findViewById(R.id.tvTraitsSummary);
            tvLocationAndTime = itemView.findViewById(R.id.tvLocationAndTime);
            tvMatchReasons = itemView.findViewById(R.id.tvMatchReasons);
            btnViewItem = itemView.findViewById(R.id.btnViewItem);
            btnStartVerify = itemView.findViewById(R.id.btnStartVerify);
        }

        void bind(PotentialMatch match) {
            // Match Score
            int score = (int) match.getSimilarityScore();
            tvMatchScore.setText(String.format(Locale.getDefault(), "%d%% Match", score));

            // Status Badge
            String status = match.getStatus();
            if ("VERIFIED_MATCH".equalsIgnoreCase(status) || "verified".equalsIgnoreCase(status)) {
                tvVerificationStatus.setText("✓ Verified Match");
                tvVerificationStatus.setBackgroundResource(R.drawable.bg_badge_found);
                tvVerificationStatus.setTextColor(ContextCompat.getColor(context, R.color.success_green));
                btnStartVerify.setText("View Verified Match");
            } else if ("UNDER_VERIFICATION".equalsIgnoreCase(status) || "under_verification".equalsIgnoreCase(status)) {
                tvVerificationStatus.setText("⏳ Under Verification");
                tvVerificationStatus.setBackgroundResource(R.drawable.bg_badge_warning);
                tvVerificationStatus.setTextColor(ContextCompat.getColor(context, R.color.warning_orange));
                btnStartVerify.setText("Continue Verification");
            } else if ("MULTIPLE_POSSIBLE_OWNERS".equalsIgnoreCase(status)) {
                tvVerificationStatus.setText("⚠ Multiple Owners");
                tvVerificationStatus.setBackgroundResource(R.drawable.bg_badge_warning);
                tvVerificationStatus.setTextColor(ContextCompat.getColor(context, R.color.warning_orange));
                btnStartVerify.setText("Provide More Proof");
            } else if ("VERIFICATION_FAILED".equalsIgnoreCase(status)) {
                tvVerificationStatus.setText("✗ Not a Match");
                tvVerificationStatus.setBackgroundResource(R.drawable.bg_badge_lost);
                tvVerificationStatus.setTextColor(ContextCompat.getColor(context, R.color.error_red));
                btnStartVerify.setText("View Details");
            } else {
                tvVerificationStatus.setText("Verification Required");
                tvVerificationStatus.setBackgroundResource(R.drawable.bg_badge_purple);
                tvVerificationStatus.setTextColor(ContextCompat.getColor(context, R.color.primary_purple));
                btnStartVerify.setText("Verify Ownership");
            }

            // Display counterpart info (default to found item details)
            String title = match.getFoundItemTitle() != null ? match.getFoundItemTitle() : match.getLostItemTitle();
            String cat = match.getFoundItemCategory() != null ? match.getFoundItemCategory() : match.getLostItemCategory();
            String imageUrl = match.getFoundItemImage() != null ? match.getFoundItemImage() : match.getLostItemImage();
            String loc = match.getFoundItemLocation() != null ? match.getFoundItemLocation() : "Location reported";
            int counterpartItemId = match.getFoundItem() > 0 ? match.getFoundItem() : match.getLostItem();

            tvItemTitle.setText(title != null ? title : "Matched Item");
            tvTraitsSummary.setText("Category: " + (cat != null ? cat.replace('_', ' ') : "Item"));
            tvLocationAndTime.setText("📍 " + loc);

            if (imageUrl != null && !imageUrl.isEmpty()) {
                Glide.with(context)
                        .load(imageUrl)
                        .placeholder(R.drawable.ic_inventory)
                        .error(R.drawable.ic_inventory)
                        .centerCrop()
                        .into(ivItemThumbnail);
            } else {
                ivItemThumbnail.setImageResource(R.drawable.ic_inventory);
            }

            // Match Breakdown Reasons
            List<String> reasons = match.getMatchReasons();
            if (reasons != null && !reasons.isEmpty()) {
                StringBuilder sb = new StringBuilder("Evidence: ");
                for (int i = 0; i < reasons.size(); i++) {
                    sb.append(reasons.get(i));
                    if (i < reasons.size() - 1) sb.append(", ");
                }
                tvMatchReasons.setText(sb.toString());
                tvMatchReasons.setVisibility(View.VISIBLE);
            } else {
                tvMatchReasons.setVisibility(View.GONE);
            }

            btnViewItem.setOnClickListener(v -> {
                if (listener != null && counterpartItemId > 0) {
                    listener.onViewItemClick(counterpartItemId);
                }
            });

            btnStartVerify.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onVerifyClick(match);
                }
            });
        }
    }
}
