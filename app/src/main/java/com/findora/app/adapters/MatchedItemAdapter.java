package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.R;
import com.findora.app.databinding.ItemMatchedBinding;
import com.findora.app.models.Item;
import com.findora.app.models.MatchedItem;
import java.util.ArrayList;
import java.util.List;

public class MatchedItemAdapter extends RecyclerView.Adapter<MatchedItemAdapter.ViewHolder> {

    public interface OnMatchClickListener {
        void onMatchClick(MatchedItem match);
    }

    private final Context context;
    private List<MatchedItem> matches = new ArrayList<>();
    private final OnMatchClickListener listener;

    public MatchedItemAdapter(Context context, OnMatchClickListener listener) {
        this.context = context;
        this.listener = listener;
    }

    public void setMatches(List<MatchedItem> matches) {
        this.matches = matches != null ? matches : new ArrayList<>();
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemMatchedBinding binding = ItemMatchedBinding.inflate(
                LayoutInflater.from(parent.getContext()), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        MatchedItem match = matches.get(position);
        holder.bind(match);
    }

    @Override
    public int getItemCount() {
        return matches.size();
    }

    class ViewHolder extends RecyclerView.ViewHolder {
        private final ItemMatchedBinding binding;

        ViewHolder(ItemMatchedBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(MatchedItem match) {
            int score = match.getMatchScore();
            binding.tvMatchScoreBadge.setText(score + "% Match");

            if (score >= 75) {
                binding.tvMatchScoreBadge.setTextColor(ContextCompat.getColor(context, R.color.success_green));
                binding.tvMatchScoreBadge.setBackgroundResource(R.drawable.bg_badge_found);
            } else {
                binding.tvMatchScoreBadge.setTextColor(ContextCompat.getColor(context, R.color.warning_orange));
                binding.tvMatchScoreBadge.setBackgroundResource(R.drawable.bg_badge_warning);
            }

            Item lost = match.getLostItem();
            Item found = match.getFoundItem();

            if (lost != null) {
                binding.tvLostTitle.setText(lost.getTitle());
                String loc = lost.getLocation() != null && !lost.getLocation().isEmpty() ? lost.getLocation() : "Unknown";
                binding.tvLostLocation.setText("Location: " + loc);
                if (lost.getCategory() != null) {
                    binding.tvCategoryPill.setText(lost.getCategory().toUpperCase());
                }
            } else {
                binding.tvLostTitle.setText("Lost Report");
                binding.tvLostLocation.setText("");
            }

            if (found != null) {
                binding.tvFoundTitle.setText(found.getTitle());
                String loc = found.getLocation() != null && !found.getLocation().isEmpty() ? found.getLocation() : "Unknown";
                binding.tvFoundLocation.setText("Location: " + loc);
            } else {
                binding.tvFoundTitle.setText("Found Report");
                binding.tvFoundLocation.setText("");
            }

            if (match.getMatchedReasons() != null && !match.getMatchedReasons().isEmpty()) {
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < match.getMatchedReasons().size(); i++) {
                    if (i > 0) sb.append(" • ");
                    sb.append(match.getMatchedReasons().get(i));
                }
                binding.tvMatchReasonSummary.setText(sb.toString());
                binding.tvMatchReasonSummary.setVisibility(android.view.View.VISIBLE);
            } else {
                binding.tvMatchReasonSummary.setVisibility(android.view.View.GONE);
            }

            if (match.getCreatedAt() != null && match.getCreatedAt().length() >= 10) {
                binding.tvMatchDate.setText(match.getCreatedAt().substring(0, 10));
            } else {
                binding.tvMatchDate.setText("");
            }

            itemView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onMatchClick(match);
                }
            });
        }
    }
}
