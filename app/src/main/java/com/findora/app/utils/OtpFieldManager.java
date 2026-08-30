package com.findora.app.utils;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.MotionEvent;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import android.widget.TextView;

import com.findora.app.R;

/**
 * Manages OTP input using the "Single Hidden EditText" pattern.
 *
 * This robust pattern guarantees perfect compatibility with all Android keyboards,
 * autofill services, clipboard paste actions, and varied screen densities by relying
 * on a single, standard EditText overlaying visual dummy boxes.
 *
 * It simulates the native focus border and blinking cursor for responsive feedback.
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
            if (isFocused) {
                isCursorVisible = !isCursorVisible;
                updateVisuals(hiddenEditText.getText().toString());
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
        setupVisualBoxesListeners();
        updateVisuals(hiddenEditText.getText().toString());
    }

    public String getOtp() {
        return hiddenEditText.getText().toString().trim();
    }

    public void clear() {
        hiddenEditText.setText("");
    }

    public void requestOtpFocus() {
        if (hiddenEditText == null) return;
        hiddenEditText.post(() -> {
            hiddenEditText.requestFocus();
            hiddenEditText.setSelection(hiddenEditText.getText().length());
            showKeyboard();
        });
    }

    public void showKeyboard() {
        if (hiddenEditText == null) return;
        InputMethodManager imm = (InputMethodManager) 
                hiddenEditText.getContext().getSystemService(Context.INPUT_METHOD_SERVICE);
        if (imm != null) {
            imm.showSoftInput(hiddenEditText, InputMethodManager.SHOW_IMPLICIT);
        }
    }

    private void setupFocusListener() {
        hiddenEditText.setOnFocusChangeListener((v, hasFocus) -> {
            isFocused = hasFocus;
            handler.removeCallbacks(cursorBlinker);
            if (hasFocus) {
                isCursorVisible = true;
                hiddenEditText.setSelection(hiddenEditText.getText().length());
                handler.postDelayed(cursorBlinker, 500);
            } else {
                isCursorVisible = false;
            }
            updateVisuals(hiddenEditText.getText().toString());
        });
        
        hiddenEditText.setOnClickListener(v -> {
            hiddenEditText.requestFocus();
            hiddenEditText.setSelection(hiddenEditText.getText().length());
            showKeyboard();
        });

        hiddenEditText.setOnTouchListener((v, event) -> {
            if (event.getAction() == MotionEvent.ACTION_UP) {
                hiddenEditText.requestFocus();
                hiddenEditText.setSelection(hiddenEditText.getText().length());
                showKeyboard();
            }
            return false;
        });
    }

    private void setupVisualBoxesListeners() {
        for (TextView box : visualBoxes) {
            box.setOnClickListener(v -> {
                hiddenEditText.requestFocus();
                hiddenEditText.setSelection(hiddenEditText.getText().length());
                showKeyboard();
            });
            box.setOnLongClickListener(v -> {
                hiddenEditText.requestFocus();
                hiddenEditText.setSelection(hiddenEditText.getText().length());
                showKeyboard();
                return hiddenEditText.performLongClick();
            });
        }
    }

    private void setupWatcher() {
        hiddenEditText.addTextChangedListener(new TextWatcher() {
            private boolean isInternalChange = false;

            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                if (isInternalChange) return;

                String input = s.toString();

                // Sanitize input: strip spaces, dashes, or non-digits (e.g. from pasted SMS / clipboard)
                String digitsOnly = input.replaceAll("[^0-9]", "");
                
                // Truncate to max OTP length
                if (digitsOnly.length() > OTP_LENGTH) {
                    digitsOnly = digitsOnly.substring(0, OTP_LENGTH);
                }

                if (!input.equals(digitsOnly)) {
                    isInternalChange = true;
                    hiddenEditText.setText(digitsOnly);
                    hiddenEditText.setSelection(digitsOnly.length());
                    isInternalChange = false;
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

    public void cleanup() {
        handler.removeCallbacks(cursorBlinker);
    }
}
