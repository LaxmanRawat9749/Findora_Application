package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.R;
import com.findora.app.databinding.ItemBadgeBinding;
import com.findora.app.models.UserBadge;
import java.util.ArrayList;
import java.util.List;

public class BadgeAdapter extends RecyclerView.Adapter<BadgeAdapter.ViewHolder> {

    private final Context context;
    private List<UserBadge> badges = new ArrayList<>();

    public BadgeAdapter(Context context) {
        this.context = context;
    }

    public void setBadges(List<UserBadge> newBadges) {
        this.badges = newBadges != null ? newBadges : new ArrayList<>();
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemBadgeBinding binding = ItemBadgeBinding.inflate(
                LayoutInflater.from(context), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        UserBadge badge = badges.get(position);
        holder.bind(badge);
    }

    @Override
    public int getItemCount() {
        return badges.size();
    }

    class ViewHolder extends RecyclerView.ViewHolder {
        private final ItemBadgeBinding binding;

        ViewHolder(ItemBadgeBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(UserBadge badge) {
            binding.tvBadgeIcon.setText(badge.getIcon());
            binding.tvBadgeName.setText(badge.getName());
            binding.tvBadgeDescription.setText(badge.getDescription());

            if (badge.isEarned()) {
                binding.cvStatusBadge.setCardBackgroundColor(
                        ContextCompat.getColor(context, R.color.light_green));
                binding.tvBadgeStatus.setTextColor(
                        ContextCompat.getColor(context, R.color.success_green));
                binding.tvBadgeStatus.setText("Unlocked ✓");
                binding.layoutProgress.setVisibility(View.GONE);
            } else {
                binding.cvStatusBadge.setCardBackgroundColor(
                        ContextCompat.getColor(context, R.color.surface_02));
                binding.tvBadgeStatus.setTextColor(
                        ContextCompat.getColor(context, R.color.text_gray));
                binding.tvBadgeStatus.setText("Locked 🔒");

                binding.layoutProgress.setVisibility(View.VISIBLE);
                binding.tvProgressFraction.setText(badge.getProgressText() != null ?
                        badge.getProgressText() : badge.getCurrentProgress() + " / " + badge.getRequiredReturns());
                binding.pbBadgeProgress.setProgress(badge.getProgressPercent());
            }
        }
    }
}
