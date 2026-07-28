package com.findora.app.views;

import android.content.Context;
import android.graphics.Matrix;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import androidx.appcompat.widget.AppCompatImageView;

public class ZoomableImageView extends AppCompatImageView {
    private Matrix matrix;
    private ScaleGestureDetector scaleGestureDetector;
    private float scaleFactor = 1.0f;
    private float lastFocusX;
    private float lastFocusY;

    public ZoomableImageView(Context context) {
        super(context);
        init(context);
    }

    public ZoomableImageView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init(context);
    }

    public ZoomableImageView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init(context);
    }

    private android.view.GestureDetector gestureDetector;
    private Runnable swipeDownCallback;

    public void setSwipeDownCallback(Runnable callback) {
        this.swipeDownCallback = callback;
    }

    private void init(Context context) {
        matrix = new Matrix();
        setScaleType(ScaleType.MATRIX);
        scaleGestureDetector = new ScaleGestureDetector(context, new ScaleListener());
        gestureDetector = new android.view.GestureDetector(context, new GestureListener());
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        scaleGestureDetector.onTouchEvent(event);
        gestureDetector.onTouchEvent(event);
        
        // Handle dragging
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                lastFocusX = event.getX();
                lastFocusY = event.getY();
                break;
            case MotionEvent.ACTION_MOVE:
                if (!scaleGestureDetector.isInProgress()) {
                    float dx = event.getX() - lastFocusX;
                    float dy = event.getY() - lastFocusY;
                    matrix.postTranslate(dx, dy);
                    setImageMatrix(matrix);
                }
                lastFocusX = event.getX();
                lastFocusY = event.getY();
                break;
        }
        return true;
    }

    private class GestureListener extends android.view.GestureDetector.SimpleOnGestureListener {
        @Override
        public boolean onDoubleTap(MotionEvent e) {
            if (scaleFactor > 1.0f) {
                scaleFactor = 1.0f;
                matrix.reset();
                setImageMatrix(matrix);
            } else {
                scaleFactor = 2.0f;
                matrix.postScale(2.0f, 2.0f, e.getX(), e.getY());
                setImageMatrix(matrix);
            }
            return true;
        }

        @Override
        public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
            if (e1 != null && e2 != null) {
                float dy = e2.getY() - e1.getY();
                float dx = e2.getX() - e1.getX();
                if (dy > 200 && Math.abs(velocityY) > Math.abs(velocityX) && swipeDownCallback != null) {
                    swipeDownCallback.run();
                    return true;
                }
            }
            return super.onFling(e1, e2, velocityX, velocityY);
        }
    }

    private class ScaleListener extends ScaleGestureDetector.SimpleOnScaleGestureListener {
        @Override
        public boolean onScale(ScaleGestureDetector detector) {
            float scale = detector.getScaleFactor();
            scaleFactor *= scale;
            scaleFactor = Math.max(0.1f, Math.min(scaleFactor, 10.0f));
            matrix.postScale(scale, scale, detector.getFocusX(), detector.getFocusY());
            setImageMatrix(matrix);
            return true;
        }
    }
}
