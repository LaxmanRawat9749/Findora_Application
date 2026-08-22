package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.R;
import com.findora.app.databinding.ItemPointTransactionBinding;
import com.findora.app.models.PointTransaction;
import com.findora.app.utils.DateUtils;
import java.util.ArrayList;
import java.util.List;

public class PointTransactionAdapter extends RecyclerView.Adapter<PointTransactionAdapter.ViewHolder> {

    private final Context context;
    private List<PointTransaction> transactions = new ArrayList<>();

    public PointTransactionAdapter(Context context) {
        this.context = context;
    }

    public void setTransactions(List<PointTransaction> newTransactions) {
        this.transactions = newTransactions != null ? newTransactions : new ArrayList<>();
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemPointTransactionBinding binding = ItemPointTransactionBinding.inflate(
                LayoutInflater.from(context), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        PointTransaction tx = transactions.get(position);
        holder.bind(tx);
    }

    @Override
    public int getItemCount() {
        return transactions.size();
    }

    class ViewHolder extends RecyclerView.ViewHolder {
        private final ItemPointTransactionBinding binding;

        ViewHolder(ItemPointTransactionBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(PointTransaction tx) {
            binding.tvPoints.setText(tx.getFormattedPoints());

            // Type styling & label
            String type = tx.getTransactionType();
            String title;
            int pointsColor;
            if (type != null) {
                switch (type) {
                    case "SUCCESSFUL_RETURN":
                        title = "🤝 Successful Return";
                        pointsColor = ContextCompat.getColor(context, R.color.primary_purple);
                        break;
                    case "FOUND_REPORT":
                        title = "📝 Found Item Report";
                        pointsColor = ContextCompat.getColor(context, R.color.success_green);
                        break;
                    case "POSITIVE_RATING":
                        title = "⭐ Positive Owner Rating";
                        pointsColor = ContextCompat.getColor(context, R.color.warning_orange);
                        break;
                    case "ADMIN_ADJUSTMENT":
                        title = "⚙️ Admin Adjustment";
                        pointsColor = ContextCompat.getColor(context, R.color.primary_purple);
                        break;
                    case "PENALTY":
                        title = "⚠️ Penalty";
                        pointsColor = ContextCompat.getColor(context, R.color.error_red);
                        break;
                    default:
                        title = type.replace('_', ' ');
                        pointsColor = ContextCompat.getColor(context, R.color.primary_purple);
                        break;
                }
            } else {
                title = "Points Awarded";
                pointsColor = ContextCompat.getColor(context, R.color.primary_purple);
            }

            binding.tvTransactionType.setText(title);
            binding.tvPoints.setTextColor(pointsColor);

            if (tx.getRelatedItemTitle() != null && !tx.getRelatedItemTitle().isEmpty()) {
                binding.tvItemTitle.setVisibility(View.VISIBLE);
                binding.tvItemTitle.setText("Item: " + tx.getRelatedItemTitle());
            } else {
                binding.tvItemTitle.setVisibility(View.GONE);
            }

            binding.tvDescription.setText(tx.getDescription() != null ? tx.getDescription() : "");

            if (tx.getCreatedAt() != null && !tx.getCreatedAt().isEmpty()) {
                binding.tvDate.setText(DateUtils.formatNotificationTime(tx.getCreatedAt()));
            } else {
                binding.tvDate.setText("");
            }
        }
    }
}
