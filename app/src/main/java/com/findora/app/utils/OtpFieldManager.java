package com.findora.app.utils;

import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.widget.EditText;
import android.widget.TextView;

import com.findora.app.R;

/**
 * Manages OTP input using the "Single Hidden EditText" pattern.
 *
 * This robust pattern guarantees perfect compatibility with all Android keyboards,
 * autofill services, and clipboard paste actions by relying on a single, standard
 * invisible EditText overlaying visual dummy boxes.
 *
 * It also manually simulates the native focus border and a blinking cursor
 * to provide clear visual feedback to the user.
 */
public class OtpFieldManager {

    public static final int OTP_LENGTH = 6;

    private final EditText hiddenEditText;
    private final TextView[] visualBoxes;
    private final OnOtpChangeListener changeListener;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean isCursorVisible = true;
    private boolean isFocused = false;

    private final Runnable cursorBlinker = new Runnable() {
        @Override
        public void run() {
            isCursorVisible = !isCursorVisible;
            updateVisuals(hiddenEditText.getText().toString());
            if (isFocused) {
                handler.postDelayed(this, 500);
            }
        }
    };

    public interface OnOtpChangeListener {
        void onOtpChange(String otp, boolean isComplete);
    }

    /**
     * @param hiddenEditText The single invisible EditText with maxLength="6"
     * @param visualBoxes    Exactly 6 visual dummy TextViews
     * @param changeListener Callback for state changes
     */
    public OtpFieldManager(EditText hiddenEditText, TextView[] visualBoxes, OnOtpChangeListener changeListener) {
        if (visualBoxes.length != OTP_LENGTH) {
            throw new IllegalArgumentException("Requires exactly " + OTP_LENGTH + " visual boxes.");
        }
        
        this.hiddenEditText = hiddenEditText;
        this.visualBoxes = visualBoxes;
        this.changeListener = changeListener;

        setupWatcher();
        setupFocusListener();
        updateVisuals(hiddenEditText.getText().toString());
    }

    public String getOtp() {
        return hiddenEditText.getText().toString().trim();
    }

    public void clear() {
        hiddenEditText.setText("");
    }

    private void setupFocusListener() {
        hiddenEditText.setOnFocusChangeListener((v, hasFocus) -> {
            isFocused = hasFocus;
            if (hasFocus) {
                isCursorVisible = true;
                handler.postDelayed(cursorBlinker, 500);
            } else {
                handler.removeCallbacks(cursorBlinker);
                isCursorVisible = false;
            }
            updateVisuals(hiddenEditText.getText().toString());
        });
        
        hiddenEditText.setOnClickListener(v -> {
            hiddenEditText.requestFocus();
            android.view.inputmethod.InputMethodManager imm = (android.view.inputmethod.InputMethodManager) 
                    hiddenEditText.getContext().getSystemService(android.content.Context.INPUT_METHOD_SERVICE);
            if (imm != null) {
                imm.showSoftInput(hiddenEditText, android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);
            }
        });
    }

    private void setupWatcher() {
        hiddenEditText.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                String input = s.toString();

                // Sanitise input: if the user pastes spaces, dashes, or letters, strip them out.
                String digitsOnly = input.replaceAll("[^0-9]", "");
                
                // Truncate to max length just in case
                if (digitsOnly.length() > OTP_LENGTH) {
                    digitsOnly = digitsOnly.substring(0, OTP_LENGTH);
                }

                if (!input.equals(digitsOnly)) {
                    // Update the EditText to contain only the digits. 
                    // This will trigger afterTextChanged again.
                    hiddenEditText.setText(digitsOnly);
                    hiddenEditText.setSelection(digitsOnly.length());
                    return; // Return early, let the recursive call handle visual updates
                }

                // Restart blinker so cursor is immediately visible upon typing
                if (isFocused) {
                    isCursorVisible = true;
                    handler.removeCallbacks(cursorBlinker);
                    handler.postDelayed(cursorBlinker, 500);
                }

                updateVisuals(digitsOnly);
                
                if (changeListener != null) {
                    changeListener.onOtpChange(digitsOnly, digitsOnly.length() == OTP_LENGTH);
                }
            }
        });
    }

    /**
     * Maps the current string onto the 6 visual dummy boxes and simulates focus/cursor state.
     */
    private void updateVisuals(String text) {
        int activeIndex = Math.min(text.length(), OTP_LENGTH - 1);
        boolean isFull = text.length() == OTP_LENGTH;

        for (int i = 0; i < OTP_LENGTH; i++) {
            boolean isActiveBox = (i == activeIndex) && isFocused;

            // 1. Manage Text & Cursor
            if (i < text.length()) {
                // If there's a character at this index, show it
                visualBoxes[i].setText(String.valueOf(text.charAt(i)));
            } else {
                // Empty box: show cursor if active, otherwise empty
                if (isActiveBox && !isFull && isCursorVisible) {
                    visualBoxes[i].setText("|");
                } else {
                    visualBoxes[i].setText("");
                }
            }

            // 2. Manage Border State
            if (isActiveBox) {
                visualBoxes[i].setBackgroundResource(R.drawable.bg_otp_box_active_dark);
            } else {
                visualBoxes[i].setBackgroundResource(R.drawable.bg_otp_box_dark);
            }
        }
    }
}
