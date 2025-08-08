plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.bharatpulse"  // Update to your app package ID if different
    compileSdk = 36
    ndkVersion = "27.0.12077973"
    
    defaultConfig {
        applicationId = "com.example.bharatpulse"  // Update to your app package ID if different
        minSdk = 21
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
        
        // To avoid lint issues on newer versions
        vectorDrawables {
            useSupportLibrary = true
        }
    }
    
    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
    }
    
    // Add the required NDK version for plugins compatibility
    ndkVersion = "27.0.12077973"
    
    // Enable View Binding if needed
    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.9.10")  // Use latest Kotlin
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.11.0")
    
    // Flutter dependencies
    implementation("io.flutter:flutter_embedding_debug:1.0.0")
}

