package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import com.findora.app.R;
import com.findora.app.databinding.ActivityVerificationBinding;
import com.findora.app.models.ConversationInitRequest;
import com.findora.app.models.ConversationInitResponse;
import com.findora.app.models.SubmitEvidenceRequest;
import com.findora.app.models.VerificationEvidence;
import com.findora.app.models.VerificationSession;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class VerificationActivity extends BaseActivity {

    public static final String EXTRA_VERIFICATION_ID = "EXTRA_VERIFICATION_ID";

    private ActivityVerificationBinding binding;
    private ApiService apiService;
    private int verificationId = -1;
    private VerificationSession currentSession;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityVerificationBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        verificationId = getIntent().getIntExtra(EXTRA_VERIFICATION_ID, -1);
        if (verificationId <= 0) {
            Toast.makeText(this, "Invalid verification session.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        binding.btnSubmitEvidence.setOnClickListener(v -> submitBlindEvidence());
        binding.btnSubmitAdditionalProof.setOnClickListener(v -> submitAdditionalProof());
        binding.btnOpenVerifiedChat.setOnClickListener(v -> openVerifiedChat());

        loadVerificationDetails();
    }

    private void loadVerificationDetails() {
        binding.progressBar.setVisibility(View.VISIBLE);

        apiService.getVerificationDetail(verificationId).enqueue(new Callback<VerificationSession>() {
            @Override
            public void onResponse(Call<VerificationSession> call, Response<VerificationSession> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    currentSession = response.body();
                    displayVerificationSession(currentSession);
                } else {
                    Toast.makeText(VerificationActivity.this, "Failed to load verification session.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<VerificationSession> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(VerificationActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void displayVerificationSession(VerificationSession session) {
        String status = session.getStatus();
        int confidence = (int) session.getVerificationConfidence();
        binding.progressBarConfidence.setProgress(confidence);
        binding.tvConfidenceScore.setText(String.format(Locale.getDefault(), "Confidence: %d%%", confidence));

        // Display Status Badges & Descriptions
        if ("VERIFIED_MATCH".equalsIgnoreCase(status) || "verified".equalsIgnoreCase(status)) {
            binding.tvStatusBadge.setText("✓ VERIFIED MATCH");
            binding.tvStatusBadge.setBackgroundResource(R.drawable.bg_badge_found);
            binding.tvStatusBadge.setTextColor(ContextCompat.getColor(this, R.color.success_green));
            binding.progressBarConfidence.setIndicatorColor(ContextCompat.getColor(this, R.color.success_green));
            binding.tvStatusDescription.setText("Ownership has been conclusively verified! Direct contact and item handover are now unlocked.");
            binding.cardVerifiedContact.setVisibility(View.VISIBLE);
            binding.cardBlindForm.setVisibility(View.GONE);
            binding.cardAdditionalProof.setVisibility(View.GONE);
        } else if ("MULTIPLE_POSSIBLE_OWNERS".equalsIgnoreCase(status)) {
            binding.tvStatusBadge.setText("⚠ MULTIPLE POSSIBLE OWNERS");
            binding.tvStatusBadge.setBackgroundResource(R.drawable.bg_badge_warning);
            binding.tvStatusBadge.setTextColor(ContextCompat.getColor(this, R.color.warning_orange));
            binding.progressBarConfidence.setIndicatorColor(ContextCompat.getColor(this, R.color.warning_orange));
            binding.tvStatusDescription.setText("Multiple reported items match generic traits. To prevent false claims, additional unique proof is required.");
            binding.cardVerifiedContact.setVisibility(View.GONE);
            binding.cardAdditionalProof.setVisibility(View.VISIBLE);
            binding.cardBlindForm.setVisibility(View.VISIBLE);
        } else if ("ADDITIONAL_PROOF_REQUIRED".equalsIgnoreCase(status) || "proof_required".equalsIgnoreCase(status)) {
            binding.tvStatusBadge.setText("⏳ PROOF REQUIRED");
            binding.tvStatusBadge.setBackgroundResource(R.drawable.bg_badge_warning);
            binding.tvStatusBadge.setTextColor(ContextCompat.getColor(this, R.color.warning_orange));
            binding.progressBarConfidence.setIndicatorColor(ContextCompat.getColor(this, R.color.warning_orange));
            binding.tvStatusDescription.setText("Evidence submitted so far is inconclusive. Please submit more detailed physical traits or proof.");
            binding.cardVerifiedContact.setVisibility(View.GONE);
            binding.cardAdditionalProof.setVisibility(View.VISIBLE);
            binding.cardBlindForm.setVisibility(View.VISIBLE);
        } else if ("VERIFICATION_FAILED".equalsIgnoreCase(status) || "failed".equalsIgnoreCase(status)) {
            binding.tvStatusBadge.setText("✗ VERIFICATION FAILED");
            binding.tvStatusBadge.setBackgroundResource(R.drawable.bg_badge_lost);
            binding.tvStatusBadge.setTextColor(ContextCompat.getColor(this, R.color.error_red));
            binding.progressBarConfidence.setIndicatorColor(ContextCompat.getColor(this, R.color.error_red));
            binding.tvStatusDescription.setText("Submitted evidence directly contradicted the physical item characteristics.");
            binding.cardVerifiedContact.setVisibility(View.GONE);
            binding.cardAdditionalProof.setVisibility(View.GONE);
            binding.cardBlindForm.setVisibility(View.VISIBLE);
        } else {
            binding.tvStatusBadge.setText("UNDER VERIFICATION");
            binding.tvStatusBadge.setBackgroundResource(R.drawable.bg_badge_purple);
            binding.tvStatusBadge.setTextColor(ContextCompat.getColor(this, R.color.primary_purple));
            binding.progressBarConfidence.setIndicatorColor(ContextCompat.getColor(this, R.color.primary_purple));
            binding.tvStatusDescription.setText("Please submit your blind physical observations below to prove ownership.");
            binding.cardVerifiedContact.setVisibility(View.GONE);
            binding.cardAdditionalProof.setVisibility(View.GONE);
            binding.cardBlindForm.setVisibility(View.VISIBLE);
        }

        // Pair Info
        String cat = session.getFoundItemCategory() != null ? session.getFoundItemCategory() :
                     (session.getLostItemCategory() != null ? session.getLostItemCategory() : "Item");

        binding.tvPairCategory.setText("Category: " + cat.replace('_', ' '));
        binding.tvLostItemSummary.setText("Lost Report: " + (session.getLostItemTitle() != null ? session.getLostItemTitle() : "Lost Item"));
        binding.tvFoundItemSummary.setText("Found Report: " + (session.getFoundItemTitle() != null ? session.getFoundItemTitle() : "Found Item"));

        // Adjust Category specific input visibility
        if ("keys".equalsIgnoreCase(cat)) {
            binding.tilKeyCount.setVisibility(View.VISIBLE);
        } else {
            binding.tilKeyCount.setVisibility(View.GONE);
        }

        // Render Evidence Logs
        renderEvidenceLogs(session.getEvidences());
    }

    private void renderEvidenceLogs(List<VerificationEvidence> evidences) {
        binding.layoutEvidenceList.removeAllViews();

        TextView title = new TextView(this);
        title.setText("Submitted Evidence Records");
        title.setTextSize(13);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        title.setTextColor(ContextCompat.getColor(this, R.color.text_dark));
        binding.layoutEvidenceList.addView(title);

        if (evidences == null || evidences.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText("No evidence submitted yet.");
            empty.setTextSize(12);
            empty.setTextColor(ContextCompat.getColor(this, R.color.text_gray));
            empty.setPadding(0, 10, 0, 0);
            binding.layoutEvidenceList.addView(empty);
            return;
        }

        for (VerificationEvidence ev : evidences) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(0, 12, 0, 12);

            TextView typeView = new TextView(this);
            String evidenceTypeStr = ev.getEvidenceType() != null ? ev.getEvidenceType().replace('_', ' ') : "Evidence";
            String submitterRole = ev.getSubmittedByRole() != null ? (" (" + ev.getSubmittedByRole() + ")") : "";
            typeView.setText("• " + evidenceTypeStr + submitterRole);
            typeView.setTextSize(12);
            typeView.setTypeface(null, android.graphics.Typeface.BOLD);
            typeView.setTextColor(ContextCompat.getColor(this, R.color.primary_purple));

            TextView valView = new TextView(this);
            valView.setText("   Value: " + (ev.getSubmittedValue() != null ? ev.getSubmittedValue() : "Submitted"));
            valView.setTextSize(12);
            valView.setTextColor(ContextCompat.getColor(this, R.color.text_dark));

            row.addView(typeView);
            row.addView(valView);

            View div = new View(this);
            div.setLayoutParams(new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 1));
            div.setBackgroundColor(ContextCompat.getColor(this, R.color.divider));

            binding.layoutEvidenceList.addView(row);
            binding.layoutEvidenceList.addView(div);
        }
    }

    private void submitBlindEvidence() {
        if (currentSession == null) return;

        String damage = binding.etDamage.getText() != null ? binding.etDamage.getText().toString().trim() : "";
        String contents = binding.etContents.getText() != null ? binding.etContents.getText().toString().trim() : "";
        String caseLock = binding.etCaseLockscreen.getText() != null ? binding.etCaseLockscreen.getText().toString().trim() : "";
        String keys = binding.etKeyCount.getText() != null ? binding.etKeyCount.getText().toString().trim() : "";
        String identifier = binding.etIdentifier.getText() != null ? binding.etIdentifier.getText().toString().trim() : "";

        if (damage.isEmpty() && contents.isEmpty() && caseLock.isEmpty() && keys.isEmpty() && identifier.isEmpty()) {
            Toast.makeText(this, "Please answer at least one verification question.", Toast.LENGTH_SHORT).show();
            return;
        }

        binding.progressBar.setVisibility(View.VISIBLE);
        binding.btnSubmitEvidence.setEnabled(false);

        // Submit each non-empty evidence
        Map<String, String> submissions = new HashMap<>();
        if (!damage.isEmpty()) submissions.put("damage_scratches", damage);
        if (!contents.isEmpty()) submissions.put("unique_contents", contents);
        if (!caseLock.isEmpty()) submissions.put("case_or_lockscreen", caseLock);
        if (!keys.isEmpty()) submissions.put("key_count_and_tags", keys);
        if (!identifier.isEmpty()) submissions.put("identifier_or_serial", identifier);

        submitEvidenceSequentially(new java.util.ArrayList<>(submissions.entrySet()), 0);
    }

    private void submitEvidenceSequentially(List<Map.Entry<String, String>> entries, int index) {
        if (index >= entries.size()) {
            binding.progressBar.setVisibility(View.GONE);
            binding.btnSubmitEvidence.setEnabled(true);
            Toast.makeText(this, "Evidence submitted and evaluated successfully!", Toast.LENGTH_LONG).show();
            // Clear inputs
            binding.etDamage.setText("");
            binding.etContents.setText("");
            binding.etCaseLockscreen.setText("");
            binding.etKeyCount.setText("");
            binding.etIdentifier.setText("");
            loadVerificationDetails();
            return;
        }

        Map.Entry<String, String> entry = entries.get(index);
        SubmitEvidenceRequest req = new SubmitEvidenceRequest(entry.getKey(), entry.getValue(), null);

        apiService.submitVerificationEvidence(verificationId, req).enqueue(new Callback<VerificationSession>() {
            @Override
            public void onResponse(Call<VerificationSession> call, Response<VerificationSession> response) {
                if (response.isSuccessful()) {
                    submitEvidenceSequentially(entries, index + 1);
                } else {
                    binding.progressBar.setVisibility(View.GONE);
                    binding.btnSubmitEvidence.setEnabled(true);
                    Toast.makeText(VerificationActivity.this, "Failed to submit evidence: " + entry.getKey(), Toast.LENGTH_SHORT).show();
                    loadVerificationDetails();
                }
            }

            @Override
            public void onFailure(Call<VerificationSession> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSubmitEvidence.setEnabled(true);
                Toast.makeText(VerificationActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void submitAdditionalProof() {
        String proof = binding.etAdditionalProof.getText() != null ? binding.etAdditionalProof.getText().toString().trim() : "";
        if (proof.isEmpty()) {
            Toast.makeText(this, "Please enter additional proof details.", Toast.LENGTH_SHORT).show();
            return;
        }

        binding.progressBar.setVisibility(View.VISIBLE);
        binding.btnSubmitAdditionalProof.setEnabled(false);

        Map<String, String> req = new HashMap<>();
        req.put("additional_proof", proof);

        apiService.provideAdditionalProof(verificationId, req).enqueue(new Callback<VerificationSession>() {
            @Override
            public void onResponse(Call<VerificationSession> call, Response<VerificationSession> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSubmitAdditionalProof.setEnabled(true);
                if (response.isSuccessful()) {
                    Toast.makeText(VerificationActivity.this, "Additional proof submitted!", Toast.LENGTH_SHORT).show();
                    binding.etAdditionalProof.setText("");
                    loadVerificationDetails();
                } else {
                    Toast.makeText(VerificationActivity.this, "Failed to submit additional proof.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<VerificationSession> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSubmitAdditionalProof.setEnabled(true);
                Toast.makeText(VerificationActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void openVerifiedChat() {
        if (currentSession == null) return;
        int targetItemId = currentSession.getFoundItem() > 0 ? currentSession.getFoundItem() : currentSession.getLostItem();
        if (targetItemId <= 0) return;

        binding.progressBar.setVisibility(View.VISIBLE);
        ConversationInitRequest req = new ConversationInitRequest(targetItemId);

        apiService.initConversation(req).enqueue(new Callback<ConversationInitResponse>() {
            @Override
            public void onResponse(Call<ConversationInitResponse> call, Response<ConversationInitResponse> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    Intent intent = new Intent(VerificationActivity.this, ChatActivity.class);
                    intent.putExtra(Constants.EXTRA_CONVERSATION_ID, response.body().getConversationId());
                    intent.putExtra("ITEM_ID", targetItemId);
                    startActivity(intent);
                } else {
                    Toast.makeText(VerificationActivity.this, "Opening chat...", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ConversationInitResponse> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(VerificationActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
