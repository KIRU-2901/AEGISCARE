// 🗣️ All translations
window.translations = {
  en: {
    // Common
    aegiscare: "AEGISCARE",
    home: "Home",
    logout: "Logout",
    loginPage: "Login Page",
    welcome: "Welcome to AEGISCARE",
    specialization: "Specialization:",
    hospital: "Hospital:",
    experience: "Experience:",
    location: "Location:",
    actions: "Actions",
    // Doctor Dashboard
    appointments: "View Appointments",
    history: "Patient History",
    prescribe: "Prescribe Medicine",
    editProfile: "Edit Profile",
    // Patient Dashboard
    chatbot: "Chatbot",
    book_appointment: "Book an Appointment",
    profile: "Profile",
    epharmacy: "E-Pharmacy",
    my_orders: "My Orders",
    patient_dashboard_desc: "Manage your health, appointments, and medicines — all in one place.",
  },

  ta: {
    // Common
    aegiscare: "ஏஜிஸ்கேர்",
    home: "முகப்பு",
    logout: "வெளியேறு",
    loginPage: "உள்நுழைவு பக்கம்",
    welcome: "ஏஜிஸ்கேருக்கு வரவேற்கிறோம்!",
    specialization: "துறை:",
    hospital: "மருத்துவமனை:",
    experience: "அனுபவம்:",
    location: "இடம்:",
    actions: "செயல்கள்",
    // Doctor Dashboard
    appointments: "நியமனங்களைப் பார்க்க",
    history: "நோயாளர் வரலாறு",
    prescribe: "மருந்து பரிந்துரை",
    editProfile: "சுயவிவரம் திருத்து",
    // Patient Dashboard
    chatbot: "அரட்டைபேசி",
    book_appointment: "நியமனம் பதிவு செய்யவும்",
    profile: "சுயவிவரம்",
    epharmacy: "மருந்தகம்",
    my_orders: "எனது ஆர்டர்கள்",
    patient_dashboard_desc: "உங்கள் ஆரோக்கியம், நியமனங்கள் மற்றும் மருந்துகளை ஒரே இடத்தில் நிர்வகிக்கலாம்.",
  },

  hin: {
    // Common
    aegiscare: "एजिसकेयर",
    home: "मुखपृष्ठ",
    logout: "लॉग आउट",
    loginPage: "लॉगिन पेज",
    welcome: "एजिसकेयर में आपका स्वागत है!",
    specialization: "विशेषज्ञता:",
    hospital: "अस्पताल:",
    experience: "अनुभव:",
    location: "स्थान:",
    actions: "क्रियाएँ",
    // Doctor Dashboard
    appointments: "अपॉइंटमेंट देखें",
    history: "मरीज का इतिहास",
    prescribe: "दवा लिखें",
    editProfile: "प्रोफ़ाइल संपादित करें",
    // Patient Dashboard
    chatbot: "चैटबॉट",
    book_appointment: "अपॉइंटमेंट बुक करें",
    profile: "प्रोफ़ाइल",
    epharmacy: "ई-फार्मेसी",
    my_orders: "मेरे ऑर्डर",
    patient_dashboard_desc: "अपना स्वास्थ्य, अपॉइंटमेंट और दवाएँ एक ही जगह प्रबंधित करें।",
  }
};

// 🌐 Change and save selected language
window.setLanguage = function(lang) {
  localStorage.setItem("language", lang);
  applyLanguage(lang);
};

// 🌍 Apply selected language to all elements
window.applyLanguage = function(lang) {
  const elements = document.querySelectorAll("[data-key]");
  elements.forEach(el => {
    const key = el.getAttribute("data-key");
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });
};

// ✅ Auto-apply saved language on page load
document.addEventListener("DOMContentLoaded", () => {
  const savedLang = localStorage.getItem("language") || "en";
  applyLanguage(savedLang);
});
