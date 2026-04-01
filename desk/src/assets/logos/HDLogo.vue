<template>
  <svg
    width="118"
    height="118"
    viewBox="0 0 118 118"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <linearGradient id="sdBgLogo" x1="0" y1="0" x2="118" y2="118" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#0E7490"/>
        <stop offset="100%" stop-color="#164E63"/>
      </linearGradient>
    </defs>
    <!-- Background: deep teal rounded square -->
    <rect width="118" height="118" rx="22" fill="url(#sdBgLogo)"/>
    <!-- Headset arc (top band) -->
    <path d="M27 64 C27 37 91 37 91 64" stroke="white" stroke-width="7" stroke-linecap="round" fill="none"/>
    <!-- Left ear cup -->
    <rect x="18" y="59" width="17" height="28" rx="8.5" fill="white"/>
    <!-- Right ear cup -->
    <rect x="83" y="59" width="17" height="28" rx="8.5" fill="white"/>
    <!-- Mic arm curving down from right ear cup -->
    <path d="M91 73 Q90 90 75 93" stroke="white" stroke-width="5.5" stroke-linecap="round" fill="none"/>
    <!-- Mic capsule -->
    <circle cx="71" cy="94" r="5.5" fill="white"/>
  </svg>
</template>
