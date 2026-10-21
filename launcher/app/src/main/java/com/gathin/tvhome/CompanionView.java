package com.gathin.tvhome;

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
    private boolean sparking = false;
    private boolean attached = false;

    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            if (!attached || getVisibility() != VISIBLE) return;
            if (sparking) return;
            if (hopping) {
                currentFrame = (currentFrame == 2) ? 3 : 2;
                invalidate();
                postDelayed(this, HOP_TICK_MS);
            } else {
                currentFrame = (currentFrame == 0) ? 1 : 0;
                invalidate();
                postDelayed(this, IDLE_TICK_MS);
            }
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

    public void setHopping(boolean isHopping) {
        if (sparking) return;
        if (this.hopping == isHopping) return;
        this.hopping = isHopping;
        removeCallbacks(ticker);
        if (isHopping) {
            currentFrame = 2; // leap forward
            invalidate();
            postDelayed(ticker, HOP_TICK_MS);
        } else {
            currentFrame = 3; // quick land touchdown
            invalidate();
            postDelayed(() -> {
                if (!hopping && !sparking) {
                    currentFrame = 0;
                    invalidate();
                    postDelayed(ticker, IDLE_TICK_MS);
                }
            }, 100);
        }
    }

    public void spark(Runnable onDone) {
        sparking = true;
        currentFrame = 4; // celebration jump with cheek sparks
        invalidate();
        animate().translationYBy(-10f * getResources().getDisplayMetrics().density)
                .setDuration(120)
                .withEndAction(() -> {
                    animate().translationYBy(10f * getResources().getDisplayMetrics().density)
                            .setDuration(120)
                            .withEndAction(() -> {
                                sparking = false;
                                currentFrame = 0;
                                invalidate();
                                if (onDone != null) onDone.run();
                                postDelayed(ticker, IDLE_TICK_MS);
                            }).start();
                }).start();
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        attached = true;
        ensureBitmap();
        postDelayed(ticker, IDLE_TICK_MS);
    }

    @Override
    protected void onDetachedFromWindow() {
        attached = false;
        removeCallbacks(ticker);
        super.onDetachedFromWindow();
    }

    @Override
    protected void onVisibilityChanged(View changedView, int visibility) {
        super.onVisibilityChanged(changedView, visibility);
        if (visibility == VISIBLE && attached) {
            removeCallbacks(ticker);
            postDelayed(ticker, IDLE_TICK_MS);
        } else {
            removeCallbacks(ticker);
        }
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
