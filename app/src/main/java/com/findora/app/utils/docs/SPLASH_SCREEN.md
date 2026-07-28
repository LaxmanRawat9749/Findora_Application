# Findora — Splash Screen & Logo Prompt
## Paste this into Antigravity Agent

---

## CONTEXT (Paste first)

```
I am building a Lost and Found Android app called Findora.
Package: com.findora.app
Language: Java + XML
Primary color: #534AB7 (purple)
Light purple: #EEEDFE
Dark purple: #3C3489
Background: #F8F7FF

The app logo is a magnifying glass with a location pin dot inside it.
This represents "searching for lost items at a location."
```

---

## PART 1 — Logo Drawable (Vector Asset)

```
Create the Findora logo as an Android vector drawable.

File: res/drawable/ic_findora_logo.xml

The logo is a magnifying glass with a map pin dot inside the lens.
Design:
- A circle (the lens) outline only, no fill
- A diagonal handle line extending from bottom-right of the lens
- A solid filled circle (dot) in the center of the lens
- A short vertical line below the dot (pin tail) inside the lens
- Everything in white color for use on dark backgrounds

XML vector drawable:
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="56dp"
    android:height="56dp"
    android:viewportWidth="56"
    android:viewportHeight="56">

    <!-- Magnifying glass circle (lens) -->
    <path
        android:pathData="M23,9 A13,13 0 1 1 23,35 A13,13 0 1 1 23,9"
        android:strokeColor="#FFFFFF"
        android:strokeWidth="3.5"
        android:fillColor="@android:color/transparent"
        android:strokeLineCap="round"/>

    <!-- Handle -->
    <path
        android:pathData="M32.5,32.5 L44,44"
        android:strokeColor="#FFFFFF"
        android:strokeWidth="3.5"
        android:fillColor="@android:color/transparent"
        android:strokeLineCap="round"/>

    <!-- Pin dot (center of lens) -->
    <path
        android:pathData="M23,17.5 A4.5,4.5 0 1 1 23,26.5 A4.5,4.5 0 1 1 23,17.5"
        android:fillColor="#FFFFFF"
        android:fillAlpha="0.9"/>

    <!-- Pin tail -->
    <path
        android:pathData="M23,26.5 L23,31"
        android:strokeColor="#FFFFFF"
        android:strokeWidth="3"
        android:fillColor="@android:color/transparent"
        android:strokeLineCap="round"/>

</vector>

Also create a purple-tinted version for light backgrounds:
File: res/drawable/ic_findora_logo_purple.xml
Same as above but strokeColor="#534AB7" and fillColor="#534AB7"

Also create the app launcher icon:
File: res/drawable/ic_launcher_foreground.xml
Same magnifying glass logo, white color, will be used on the purple
adaptive icon background.
```

---

## PART 2 — Splash Screen Activity

```
Build the Splash Screen for Findora. Create:
1. activities/SplashActivity.java
2. res/layout/activity_splash.xml

━━━ XML LAYOUT (activity_splash.xml) ━━━

Root: ConstraintLayout
- layout_width: match_parent
- layout_height: match_parent
- background: #534AB7

Decorative ring 1 (large circle behind logo):
ImageView or View:
- width: 280dp, height: 280dp
- background: @drawable/circle_ring_large
- alpha: 0.10
- centered horizontally
- centered vertically with offset -40dp (slightly above center)
- id: ivRing1

Decorative ring 2 (medium circle):
ImageView or View:
- width: 200dp, height: 200dp
- background: @drawable/circle_ring_medium
- alpha: 0.07
- centered same as ring 1
- id: ivRing2

Logo container (LinearLayout vertical, centered):
- id: layoutLogo
- orientation: vertical
- gravity: center
- alpha: 0 (starts invisible, animates in)
- constrained to center of parent

  Logo card (CardView inside layoutLogo):
  - width: 88dp, height: 88dp
  - cardCornerRadius: 24dp
  - cardElevation: 0dp
  - cardBackgroundColor: rgba(255,255,255,0.15) → use #26FFFFFF
  - id: cardLogo

    ImageView inside cardLogo:
    - src: @drawable/ic_findora_logo
    - width: 56dp, height: 56dp
    - centered in card

  App name TextView (below CardView, marginTop 20dp):
  - id: tvAppName
  - text: "Findora"
  - textSize: 32sp
  - textColor: #FFFFFF
  - textStyle: normal (weight 500 via fontWeight)
  - letterSpacing: 0.02
  - gravity: center

  Tagline TextView (below app name, marginTop 4dp):
  - id: tvTagline
  - text: "LOST & FOUND"
  - textSize: 11sp
  - textColor: #99FFFFFF (white 60% alpha)
  - letterSpacing: 0.15
  - gravity: center

Loading dots row (LinearLayout horizontal, centered, marginTop 40dp):
- id: layoutDots
- gravity: center
- gap: 8dp between dots

  Three Views (dots):
  - id: dot1, dot2, dot3
  - width: 7dp, height: 7dp each
  - background: @drawable/circle_dot_white
  - alpha: 0.3 initially

Bottom tagline (TextView at bottom of screen):
- id: tvBottomTagline
- text: "Recover what matters most"
- textSize: 12sp
- textColor: #66FFFFFF (white 40% alpha)
- gravity: center
- constrain to bottom with margin 40dp

━━━ DRAWABLES NEEDED ━━━

Create res/drawable/circle_ring_large.xml:
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <stroke android:width="1dp" android:color="#FFFFFF"/>
    <size android:width="280dp" android:height="280dp"/>
</shape>

Create res/drawable/circle_ring_medium.xml:
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <stroke android:width="1dp" android:color="#FFFFFF"/>
    <size android:width="200dp" android:height="200dp"/>
</shape>

Create res/drawable/circle_dot_white.xml:
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#FFFFFF"/>
    <size android:width="7dp" android:height="7dp"/>
</shape>

━━━ JAVA (SplashActivity.java) ━━━

Package: com.findora.app.activities

Fields:
LinearLayout layoutLogo;
View dot1, dot2, dot3;
Handler handler = new Handler();
SessionManager sessionManager;

onCreate:
- setContentView(R.layout.activity_splash)
- Hide the action bar: getSupportActionBar().hide() or in theme
- Make status bar transparent (full screen immersive):
  getWindow().setFlags(
    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
  )
- sessionManager = new SessionManager(this)
- Bind views
- startAnimations()
- handler.postDelayed(this::navigateNext, 3000)

startAnimations():
  Step 1 — Logo fades up into view (starts after 200ms):
  handler.postDelayed(() -> {
    layoutLogo.animate()
      .alpha(1f)
      .translationY(0f)
      .setDuration(600)
      .setInterpolator(new DecelerateInterpolator())
      .start();
    layoutLogo.setTranslationY(30f); // start 30dp below
  }, 200);

  Step 2 — Dots animate one by one with pulse (starts after 800ms):
  View[] dots = {dot1, dot2, dot3};
  for (int i = 0; i < 3; i++) {
    final int index = i;
    handler.postDelayed(() -> {
      animateDot(dots[index]);
    }, 800 + (index * 150));
  }

animateDot(View dot):
  ObjectAnimator pulseAlpha = ObjectAnimator.ofFloat(dot, "alpha", 0.3f, 1f, 0.3f);
  ObjectAnimator pulseScale = ObjectAnimator.ofPropertyValuesHolder(dot,
    PropertyValuesHolder.ofFloat("scaleX", 0.7f, 1f, 0.7f),
    PropertyValuesHolder.ofFloat("scaleY", 0.7f, 1f, 0.7f)
  );
  AnimatorSet set = new AnimatorSet();
  set.playTogether(pulseAlpha, pulseScale);
  set.setDuration(800);
  set.setRepeatCount(ValueAnimator.INFINITE) on each animator;
  set.start();

navigateNext():
  Intent intent;
  if (sessionManager.isLoggedIn()) {
    if (sessionManager.isAdmin()) {
      intent = new Intent(this, AdminActivity.class);
    } else {
      intent = new Intent(this, HomeActivity.class);
    }
  } else {
    intent = new Intent(this, LoginActivity.class);
  }
  intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
  startActivity(intent);
  // Smooth transition
  overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
  finish();

onDestroy:
  handler.removeCallbacksAndMessages(null);
```

---

## PART 3 — Splash Screen Theme (No Action Bar)

```
Update res/values/styles.xml or res/values/themes.xml to add a
splash-specific theme that hides the action bar and status bar.

Add this theme:
<style name="Theme.Findora.Splash" parent="Theme.Findora">
    <item name="windowActionBar">false</item>
    <item name="windowNoTitle">true</item>
    <item name="android:windowFullscreen">true</item>
    <item name="android:windowBackground">#534AB7</item>
    <item name="android:statusBarColor">#534AB7</item>
    <item name="android:navigationBarColor">#534AB7</item>
</style>

Then in AndroidManifest.xml update SplashActivity to use this theme:
<activity
    android:name=".activities.SplashActivity"
    android:theme="@style/Theme.Findora.Splash"
    android:exported="true"
    android:screenOrientation="portrait">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>

Also make sure LoginActivity is no longer the LAUNCHER — remove its
intent-filter and keep it as a plain activity:
<activity android:name=".activities.LoginActivity" />
```

---

## PART 4 — App Launcher Icon (Adaptive Icon)

```
Update the app launcher icon to use the Findora logo.

Create res/drawable/ic_launcher_background.xml:
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#534AB7"/>
</shape>

Create res/drawable/ic_launcher_foreground.xml:
The Findora magnifying glass + pin logo in white color
(same as ic_findora_logo.xml but sized for adaptive icon)

Update res/mipmap-anydpi-v26/ic_launcher.xml:
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>

Update res/mipmap-anydpi-v26/ic_launcher_round.xml:
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>

Also update AndroidManifest.xml application tag:
android:icon="@mipmap/ic_launcher"
android:roundIcon="@mipmap/ic_launcher_round"
android:label="Findora"
```

---

## PART 5 — Smooth Screen Transition Animation

```
Add smooth fade transition from Splash to Login/Home screen.

Create res/anim/fade_in_slow.xml:
<?xml version="1.0" encoding="utf-8"?>
<alpha xmlns:android="http://schemas.android.com/apk/res/android"
    android:interpolator="@android:anim/decelerate_interpolator"
    android:fromAlpha="0.0"
    android:toAlpha="1.0"
    android:duration="500"/>

Create res/anim/fade_out_slow.xml:
<?xml version="1.0" encoding="utf-8"?>
<alpha xmlns:android="http://schemas.android.com/apk/res/android"
    android:interpolator="@android:anim/accelerate_interpolator"
    android:fromAlpha="1.0"
    android:toAlpha="0.0"
    android:duration="300"/>

In SplashActivity.navigateNext() replace:
overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);

With:
overridePendingTransition(R.anim.fade_in_slow, R.anim.fade_out_slow);
```

---

## COMPLETE FLOW SUMMARY

After implementing all 5 parts, the app launch flow is:

1. User taps Findora app icon (purple background + magnifying glass logo)
2. Splash screen appears with purple background
3. Logo card + "Findora" text fades up smoothly (600ms)
4. Three white dots pulse in sequence
5. "Recover what matters most" shows at bottom
6. After 3 seconds → check SessionManager.isLoggedIn()
   - YES → HomeActivity or AdminActivity (smooth fade transition)
   - NO → LoginActivity (smooth fade transition)

---

## ERROR FIX TEMPLATE (if needed)

```
I am implementing the Findora splash screen in Android Java.
Package: com.findora.app.activities
The SplashActivity uses Handler for delay and ObjectAnimator for animations.

Error:
[PASTE ERROR HERE]

File: [FILE NAME]

Fix only this specific error.
```

---

## DESIGN SPECS REFERENCE

| Element | Value |
|---------|-------|
| Splash background | #534AB7 |
| Logo card size | 88 × 88 dp |
| Logo card corner radius | 24 dp |
| Logo card background | rgba(255,255,255,0.15) |
| Logo icon size | 56 × 56 dp |
| App name text size | 32sp |
| App name color | #FFFFFF |
| Tagline text | "LOST & FOUND" |
| Tagline size | 11sp / letter-spacing 0.15 |
| Tagline color | #99FFFFFF (60% alpha) |
| Loading dots | 7dp circles, white |
| Dot animation | Pulse scale 0.7→1→0.7 |
| Bottom tagline | "Recover what matters most" |
| Bottom tagline size | 12sp / #66FFFFFF |
| Splash duration | 3000ms |
| Fade in animation | 600ms decelerate |
| Transition to next | fade_in + fade_out |
| Launcher icon | Purple bg + white logo |
| Status bar color | #534AB7 (matches splash) |

*Paste the CONTEXT block first, then each PART one at a time. Test after each part.*