package com.gathin.tvhome;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.View;

/**
 * Animated retro focus companion that hops between tiles alongside the spring highlight.
 * Frames: 0=Idle Neutral, 1=Idle Wag, 2=Hop Leap, 3=Hop Land, 4=Select Spark.
 */
public class CompanionView extends View {

    private static final int FRAME_COUNT = 5;
    private static final long IDLE_TICK_MS = 600;
    private static final long HOP_TICK_MS = 140;
    private static final long SPARK_MS = 280;

    private Bitmap strip;
    private int frameW;
    private int frameH;
    private final Rect srcRect = new Rect();
    private final RectF dstRect = new RectF();
    private final Paint paint = new Paint();

    private int currentFrame = 0;
    private boolean hopping = false;
    private boolean attached = false;
    /** Height of the select hop in px: kept apart from translationY, which the focus springs own. */
    private float lift = 0f;
    private ValueAnimator sparkAnimator;

    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            if (!isRunning() || isSparking()) return;
            if (hopping) {
                currentFrame = (currentFrame == 2) ? 3 : 2;
                schedule(this, HOP_TICK_MS);
            } else {
                currentFrame = (currentFrame == 0) ? 1 : 0;
                schedule(this, IDLE_TICK_MS);
            }
            invalidate();
        }
    };

    /** Touchdown frame after a hop, then back to idle. */
    private final Runnable land = new Runnable() {
        @Override
        public void run() {
            if (hopping || isSparking()) return;
            currentFrame = 0;
            invalidate();
            schedule(ticker, IDLE_TICK_MS);
        }
    };

    public CompanionView(Context context, AttributeSet attrs) {
        super(context, attrs);
        paint.setFilterBitmap(false); // keep retro 16-bit pixel art crisp
        paint.setDither(false);
        setLayerType(LAYER_TYPE_HARDWARE, null);
    }

    private void ensureBitmap() {
        if (strip == null) {
            BitmapFactory.Options opts = new BitmapFactory.Options();
            opts.inScaled = false;
            strip = BitmapFactory.decodeResource(getResources(), R.drawable.companion_strip, opts);
            if (strip != null) {
                frameW = strip.getWidth() / FRAME_COUNT;
                frameH = strip.getHeight();
            }
        }
    }

    private boolean isSparking() {
        return sparkAnimator != null;
    }

    /** Frames only advance while the view is attached, visible and its window is in front. */
    private boolean isRunning() {
        return attached && getVisibility() == VISIBLE && getWindowVisibility() == VISIBLE;
    }

    /** One pending callback per runnable, so quick state changes never stack up parallel tick chains. */
    private void schedule(Runnable r, long delay) {
        removeCallbacks(r);
        postDelayed(r, delay);
    }

    private void stopTicking() {
        removeCallbacks(ticker);
        removeCallbacks(land);
    }

    private void restartTicking() {
        stopTicking();
        if (isRunning() && !isSparking()) schedule(ticker, hopping ? HOP_TICK_MS : IDLE_TICK_MS);
    }

    public void setHopping(boolean isHopping) {
        if (this.hopping == isHopping) return;
        this.hopping = isHopping;
        if (isSparking()) return;   // the spark ends in the right pose for the new state
        stopTicking();
        if (isHopping) {
            currentFrame = 2; // leap forward
            invalidate();
            schedule(ticker, HOP_TICK_MS);
        } else {
            currentFrame = 3; // quick land touchdown
            invalidate();
            schedule(land, 100);
        }
    }

    /** The view's translationY without the select hop: what the focus springs read and write. */
    public float getRestY() {
        return getTranslationY() + lift;
    }

    public void setRestY(float y) {
        setTranslationY(y - lift);
    }

    private void setLift(float value) {
        setTranslationY(getTranslationY() + lift - value);
        lift = value;
    }

    /** Select celebration. {@code hop} false (animations off) only swaps the sprite frame. */
    public void spark(boolean hop) {
        cancelSpark();
        stopTicking();
        currentFrame = 4; // celebration jump with cheek sparks
        invalidate();
        float peak = hop ? 10f * getResources().getDisplayMetrics().density : 0f;
        ValueAnimator a = ValueAnimator.ofFloat(0f, peak, 0f);
        a.setDuration(SPARK_MS);
        a.addUpdateListener(v -> setLift((Float) v.getAnimatedValue()));
        // Also runs on cancel, so a hidden or restarted companion never keeps its lift or the spark frame.
        a.addListener(new AnimatorListenerAdapter() {
            @Override
            public void onAnimationEnd(Animator animation) {
                if (sparkAnimator != animation) return;
                sparkAnimator = null;
                setLift(0f);
                currentFrame = hopping ? 2 : 0;
                invalidate();
                restartTicking();
            }
        });
        sparkAnimator = a;
        a.start();
    }

    /** Ends a running spark at once, putting the view back on its rest position. */
    public void cancelSpark() {
        if (sparkAnimator != null) sparkAnimator.cancel();
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        attached = true;
        ensureBitmap();
        restartTicking();
    }

    @Override
    protected void onDetachedFromWindow() {
        attached = false;
        cancelSpark();
        stopTicking();
        super.onDetachedFromWindow();
    }

    @Override
    protected void onVisibilityChanged(View changedView, int visibility) {
        super.onVisibilityChanged(changedView, visibility);
        restartTicking();
    }

    @Override
    protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);
        restartTicking();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        ensureBitmap();
        if (strip == null || frameW <= 0) return;

        int f = Math.max(0, Math.min(currentFrame, FRAME_COUNT - 1));
        srcRect.set(f * frameW, 0, (f + 1) * frameW, frameH);
        dstRect.set(0, 0, getWidth(), getHeight());
        canvas.drawBitmap(strip, srcRect, dstRect, paint);
    }
}
