package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.io.Serializable;
import java.util.List;

public class CategoryVerificationSchema implements Serializable {
    private String label;
    @SerializedName("has_identifier")
    private boolean hasIdentifier;
    @SerializedName("identifier_name")
    private String identifierName;
    @SerializedName("blind_prompts")
    private List<Prompt> blindPrompts;
    @SerializedName("proof_types")
    private List<String> proofTypes;

    public static class Prompt implements Serializable {
        private String key;
        @SerializedName("finder_prompt")
        private String finderPrompt;
        @SerializedName("owner_prompt")
        private String ownerPrompt;
        private String weight;

        public Prompt() {}

        public String getKey() { return key; }
        public void setKey(String key) { this.key = key; }

        public String getFinderPrompt() { return finderPrompt; }
        public void setFinderPrompt(String finderPrompt) { this.finderPrompt = finderPrompt; }

        public String getOwnerPrompt() { return ownerPrompt; }
        public void setOwnerPrompt(String ownerPrompt) { this.ownerPrompt = ownerPrompt; }

        public String getWeight() { return weight; }
        public void setWeight(String weight) { this.weight = weight; }
    }

    public CategoryVerificationSchema() {}

    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }

    public boolean isHasIdentifier() { return hasIdentifier; }
    public void setHasIdentifier(boolean hasIdentifier) { this.hasIdentifier = hasIdentifier; }

    public String getIdentifierName() { return identifierName; }
    public void setIdentifierName(String identifierName) { this.identifierName = identifierName; }

    public List<Prompt> getBlindPrompts() { return blindPrompts; }
    public void setBlindPrompts(List<Prompt> blindPrompts) { this.blindPrompts = blindPrompts; }

    public List<String> getProofTypes() { return proofTypes; }
    public void setProofTypes(List<String> proofTypes) { this.proofTypes = proofTypes; }
}
