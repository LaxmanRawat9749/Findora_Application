package com.findora.app.activities;

import android.os.Bundle;
import android.widget.ImageView;
import androidx.appcompat.app.AppCompatActivity;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.views.ZoomableImageView;

public class FullScreenImageActivity extends AppCompatActivity {
    public static final String EXTRA_IMAGE_URL = "image_url";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_full_screen_image);

        ZoomableImageView ivFullScreen = findViewById(R.id.ivFullScreen);
        ImageView ivClose = findViewById(R.id.ivClose);

        ivClose.setOnClickListener(v -> finish());

        String imageUrl = getIntent().getStringExtra(EXTRA_IMAGE_URL);
        if (imageUrl != null) {
            com.findora.app.utils.GlideImageHelper.loadFullScreenImage(this, imageUrl, ivFullScreen);
        }

    }
}
