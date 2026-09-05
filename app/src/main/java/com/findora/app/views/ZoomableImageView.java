package com.findora.app.views;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Matrix;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.util.AttributeSet;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.animation.DecelerateInterpolator;
import androidx.annotation.Nullable;
import androidx.appcompat.widget.AppCompatImageView;

public class ZoomableImageView extends AppCompatImageView {

    private static final int NONE = 0;
    private static final int DRAG = 1;
    private static final int ZOOM = 2;

    private final Matrix matrix = new Matrix();
    private final float[] matrixValues = new float[9];

    private ScaleGestureDetector scaleGestureDetector;
    private GestureDetector gestureDetector;

    private float currentZoom = 1.0f;
    private float minZoom = 1.0f;
    private float maxZoom = 5.0f;
    private float baseScale = 1.0f;

    private int viewWidth = 0;
    private int viewHeight = 0;
    private int drawableWidth = 0;
    private int drawableHeight = 0;

    private float lastTouchX;
    private float lastTouchY;
    private int activePointerId = MotionEvent.INVALID_POINTER_ID;
    private int touchMode = NONE;

    private ValueAnimator zoomAnimator;
    private Runnable swipeDownCallback;

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

    public void setSwipeDownCallback(Runnable callback) {
        this.swipeDownCallback = callback;
    }

    private void init(Context context) {
        setScaleType(ScaleType.MATRIX);
        scaleGestureDetector = new ScaleGestureDetector(context, new ScaleListener());
        gestureDetector = new GestureDetector(context, new GestureListener());
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        if (w > 0 && h > 0) {
            viewWidth = w;
            viewHeight = h;
            initFitCenter();
        }
    }

    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        super.onLayout(changed, left, top, right, bottom);
        if (changed) {
            viewWidth = right - left;
            viewHeight = bottom - top;
            if (currentZoom <= 1.05f) {
                initFitCenter();
            } else {
                fixTranslation();
                setImageMatrix(matrix);
            }
        }
    }

    @Override
    public void setImageDrawable(@Nullable Drawable drawable) {
        super.setImageDrawable(drawable);
        updateDrawableDimensions();
        initFitCenter();
    }

    @Override
    public void setImageBitmap(Bitmap bm) {
        super.setImageBitmap(bm);
        updateDrawableDimensions();
        initFitCenter();
    }

    @Override
    public void setImageResource(int resId) {
        super.setImageResource(resId);
        updateDrawableDimensions();
        initFitCenter();
    }

    @Override
    public void setImageURI(@Nullable Uri uri) {
        super.setImageURI(uri);
        updateDrawableDimensions();
        initFitCenter();
    }

    private void updateDrawableDimensions() {
        Drawable drawable = getDrawable();
        if (drawable != null) {
            drawableWidth = drawable.getIntrinsicWidth();
            drawableHeight = drawable.getIntrinsicHeight();
        } else {
            drawableWidth = 0;
            drawableHeight = 0;
        }
    }

    public void initFitCenter() {
        Drawable drawable = getDrawable();
        if (drawable == null) return;

        updateDrawableDimensions();
        if (drawableWidth <= 0 || drawableHeight <= 0 || viewWidth <= 0 || viewHeight <= 0) {
            return;
        }

        float scaleX = (float) viewWidth / (float) drawableWidth;
        float scaleY = (float) viewHeight / (float) drawableHeight;
        baseScale = Math.min(scaleX, scaleY);

        float redundantX = viewWidth - (baseScale * drawableWidth);
        float redundantY = viewHeight - (baseScale * drawableHeight);
        float transX = redundantX / 2.0f;
        float transY = redundantY / 2.0f;

        matrix.reset();
        matrix.setScale(baseScale, baseScale);
        matrix.postTranslate(transX, transY);
        currentZoom = 1.0f;

        setImageMatrix(matrix);
    }

    private void fixTranslation() {
        if (drawableWidth <= 0 || drawableHeight <= 0 || viewWidth <= 0 || viewHeight <= 0) return;

        matrix.getValues(matrixValues);
        float transX = matrixValues[Matrix.MTRANS_X];
        float transY = matrixValues[Matrix.MTRANS_Y];
        float scaleX = matrixValues[Matrix.MSCALE_X];
        float scaleY = matrixValues[Matrix.MSCALE_Y];

        float currentWidth = drawableWidth * scaleX;
        float currentHeight = drawableHeight * scaleY;

        float deltaX = 0f;
        float deltaY = 0f;

        // Constrain X
        if (currentWidth <= viewWidth) {
            float targetX = (viewWidth - currentWidth) / 2.0f;
            deltaX = targetX - transX;
        } else {
            if (transX > 0) {
                deltaX = -transX;
            } else if (transX + currentWidth < viewWidth) {
                deltaX = viewWidth - (transX + currentWidth);
            }
        }

        // Constrain Y
        if (currentHeight <= viewHeight) {
            float targetY = (viewHeight - currentHeight) / 2.0f;
            deltaY = targetY - transY;
        } else {
            if (transY > 0) {
                deltaY = -transY;
            } else if (transY + currentHeight < viewHeight) {
                deltaY = viewHeight - (transY + currentHeight);
            }
        }

        if (deltaX != 0 || deltaY != 0) {
            matrix.postTranslate(deltaX, deltaY);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        scaleGestureDetector.onTouchEvent(event);
        gestureDetector.onTouchEvent(event);

        int action = event.getActionMasked();
        switch (action) {
            case MotionEvent.ACTION_DOWN:
                if (zoomAnimator != null && zoomAnimator.isRunning()) {
                    zoomAnimator.cancel();
                }
                lastTouchX = event.getX();
                lastTouchY = event.getY();
                activePointerId = event.getPointerId(0);
                touchMode = DRAG;
                break;

            case MotionEvent.ACTION_POINTER_DOWN:
                touchMode = ZOOM;
                break;

            case MotionEvent.ACTION_MOVE:
                if (touchMode == DRAG && !scaleGestureDetector.isInProgress()) {
                    int pointerIndex = event.findPointerIndex(activePointerId);
                    if (pointerIndex != -1) {
                        float x = event.getX(pointerIndex);
                        float y = event.getY(pointerIndex);
                        float dx = x - lastTouchX;
                        float dy = y - lastTouchY;

                        if (currentZoom > 1.0f) {
                            matrix.postTranslate(dx, dy);
                            fixTranslation();
                            setImageMatrix(matrix);
                        }

                        lastTouchX = x;
                        lastTouchY = y;
                    }
                }
                break;

            case MotionEvent.ACTION_POINTER_UP:
                int pointerIndex = event.getActionIndex();
                int pointerId = event.getPointerId(pointerIndex);
                if (pointerId == activePointerId) {
                    int newPointerIndex = (pointerIndex == 0) ? 1 : 0;
                    if (newPointerIndex < event.getPointerCount()) {
                        lastTouchX = event.getX(newPointerIndex);
                        lastTouchY = event.getY(newPointerIndex);
                        activePointerId = event.getPointerId(newPointerIndex);
                    }
                }
                break;

            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                touchMode = NONE;
                activePointerId = MotionEvent.INVALID_POINTER_ID;
                if (currentZoom < minZoom) {
                    resetZoomSmoothly();
                } else {
                    fixTranslation();
                    setImageMatrix(matrix);
                }
                break;
        }
        return true;
    }

    private void animateZoom(float targetZoom, float focusX, float focusY) {
        if (zoomAnimator != null && zoomAnimator.isRunning()) {
            zoomAnimator.cancel();
        }

        final float startZoom = currentZoom;
        zoomAnimator = ValueAnimator.ofFloat(startZoom, targetZoom);
        zoomAnimator.setDuration(250);
        zoomAnimator.setInterpolator(new DecelerateInterpolator());
        zoomAnimator.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
            private float lastStepZoom = startZoom;

            @Override
            public void onAnimationUpdate(ValueAnimator animation) {
                float animatedZoom = (Float) animation.getAnimatedValue();
                float factor = animatedZoom / lastStepZoom;
                currentZoom = animatedZoom;
                lastStepZoom = animatedZoom;

                matrix.postScale(factor, factor, focusX, focusY);
                fixTranslation();
                setImageMatrix(matrix);
            }
        });
        zoomAnimator.start();
    }

    public void resetZoomSmoothly() {
        if (viewWidth <= 0 || viewHeight <= 0 || drawableWidth <= 0 || drawableHeight <= 0) return;

        float scaleX = (float) viewWidth / (float) drawableWidth;
        float scaleY = (float) viewHeight / (float) drawableHeight;
        final float targetBaseScale = Math.min(scaleX, scaleY);
        float redundantX = viewWidth - (targetBaseScale * drawableWidth);
        float redundantY = viewHeight - (targetBaseScale * drawableHeight);
        final float targetTransX = redundantX / 2.0f;
        final float targetTransY = redundantY / 2.0f;

        matrix.getValues(matrixValues);
        final float startTransX = matrixValues[Matrix.MTRANS_X];
        final float startTransY = matrixValues[Matrix.MTRANS_Y];
        final float startScale = matrixValues[Matrix.MSCALE_X];

        if (zoomAnimator != null && zoomAnimator.isRunning()) {
            zoomAnimator.cancel();
        }

        zoomAnimator = ValueAnimator.ofFloat(0f, 1f);
        zoomAnimator.setDuration(250);
        zoomAnimator.setInterpolator(new DecelerateInterpolator());
        zoomAnimator.addUpdateListener(animation -> {
            float fraction = animation.getAnimatedFraction();
            float currentScaleVal = startScale + fraction * (targetBaseScale - startScale);
            float currentTransXVal = startTransX + fraction * (targetTransX - startTransX);
            float currentTransYVal = startTransY + fraction * (targetTransY - startTransY);

            matrix.reset();
            matrix.setScale(currentScaleVal, currentScaleVal);
            matrix.postTranslate(currentTransXVal, currentTransYVal);
            currentZoom = 1.0f;
            setImageMatrix(matrix);
        });
        zoomAnimator.start();
    }

    private class GestureListener extends GestureDetector.SimpleOnGestureListener {
        @Override
        public boolean onDoubleTap(MotionEvent e) {
            if (currentZoom > 1.05f) {
                resetZoomSmoothly();
            } else {
                animateZoom(2.5f, e.getX(), e.getY());
            }
            return true;
        }

        @Override
        public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
            if (currentZoom <= 1.05f && e1 != null && e2 != null) {
                float dy = e2.getY() - e1.getY();
                float dx = e2.getX() - e1.getX();
                if (dy > 150 && Math.abs(velocityY) > Math.abs(velocityX) && swipeDownCallback != null) {
                    swipeDownCallback.run();
                    return true;
                }
            }
            return super.onFling(e1, e2, velocityX, velocityY);
        }
    }

    private class ScaleListener extends ScaleGestureDetector.SimpleOnScaleGestureListener {
        @Override
        public boolean onScaleBegin(ScaleGestureDetector detector) {
            touchMode = ZOOM;
            return true;
        }

        @Override
        public boolean onScale(ScaleGestureDetector detector) {
            float scaleFactor = detector.getScaleFactor();
            float prevZoom = currentZoom;
            currentZoom *= scaleFactor;

            if (currentZoom > maxZoom) {
                currentZoom = maxZoom;
                scaleFactor = maxZoom / prevZoom;
            } else if (currentZoom < minZoom) {
                currentZoom = minZoom;
                scaleFactor = minZoom / prevZoom;
            }

            if (scaleFactor != 1.0f) {
                matrix.postScale(scaleFactor, scaleFactor, detector.getFocusX(), detector.getFocusY());
                fixTranslation();
                setImageMatrix(matrix);
            }
            return true;
        }
    }
}
