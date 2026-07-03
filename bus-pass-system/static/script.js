// Global JavaScript functions
document.addEventListener("DOMContentLoaded", () => {
  // Initialize all components
  initializeTheme()
  initializeAlerts()
  initializeForms()
  initializeModals()
  initializeSlideshow()
  updatePaymentFields()
  // Initialize map if on about page
  if (document.getElementById("map")) {
    initializeMap()
  }
})

// Theme handling
function initializeTheme() {
  const savedTheme = localStorage.getItem("theme") || "light"
  document.documentElement.setAttribute("data-theme", savedTheme)
  updateThemeToggleLabel(savedTheme)
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme") || "light"
  const nextTheme = currentTheme === "dark" ? "light" : "dark"

  document.documentElement.setAttribute("data-theme", nextTheme)
  localStorage.setItem("theme", nextTheme)
  updateThemeToggleLabel(nextTheme)
}

function updateThemeToggleLabel(theme) {
  const label = document.getElementById("theme-toggle-label")
  if (label) {
    label.textContent = theme === "dark" ? "Light" : "Dark"
  }
}

// Alert handling
function initializeAlerts() {
  const alerts = document.querySelectorAll(".alert")
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = "0"
      setTimeout(() => {
        alert.remove()
      }, 300)
    }, 5000)
  })
}

// Form handling
function initializeForms() {
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const submitBtn = form.querySelector('button[type="submit"]')
      if (submitBtn) {
        submitBtn.disabled = true
        submitBtn.textContent = "Processing..."

        setTimeout(() => {
          submitBtn.disabled = false
          submitBtn.textContent = submitBtn.getAttribute("data-original-text") || "Submit"
        }, 3000)
      }
    })
  })
}

// Modal handling
function initializeModals() {
  const modalTriggers = document.querySelectorAll("[data-modal]")
  modalTriggers.forEach((trigger) => {
    trigger.addEventListener("click", function (e) {
      e.preventDefault()
      const modalId = this.getAttribute("data-modal")
      const modal = document.getElementById(modalId)
      if (modal) {
        modal.style.display = "block"
      }
    })
  })

  const modalCloses = document.querySelectorAll(".modal-close")
  modalCloses.forEach((close) => {
    close.addEventListener("click", function () {
      const modal = this.closest(".modal")
      if (modal) {
        modal.style.display = "none"
      }
    })
  })
}

// Generate Pass function
function generatePass(username) {
  showLoading()

  fetch(`/generate_pass/${username}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading()
      if (data.success) {
        showAlert("Pass generated successfully!", "success")
        location.reload()
      } else {
        showAlert(data.error || "Failed to generate pass", "error")
      }
    })
    .catch((error) => {
      hideLoading()
      showAlert("Network error occurred", "error")
      console.error("Error:", error)
    })
}

// Make Payment function
function updatePaymentFields() {
  const paymentMethod = document.getElementById("payment_method")
  const mobileFields = document.getElementById("mobile-payment-fields")
  const bankFields = document.getElementById("bank-payment-fields")
  const paypalFields = document.getElementById("paypal-payment-fields")

  if (!paymentMethod || !mobileFields || !bankFields || !paypalFields) return

  if (paymentMethod.value === "Bank Transfer") {
    mobileFields.classList.add("payment-fields-hidden")
    bankFields.classList.remove("payment-fields-hidden")
    paypalFields.classList.add("payment-fields-hidden")
  } else if (paymentMethod.value === "PayPal") {
    mobileFields.classList.add("payment-fields-hidden")
    bankFields.classList.add("payment-fields-hidden")
    paypalFields.classList.remove("payment-fields-hidden")
  } else {
    mobileFields.classList.remove("payment-fields-hidden")
    bankFields.classList.add("payment-fields-hidden")
    paypalFields.classList.add("payment-fields-hidden")
  }
}

function makePayment(username) {
  const amount = document.getElementById("amount").value
  const paymentMethod = document.getElementById("payment_method").value
  const formData = new FormData()

  if (!amount || amount < 50) {
    showAlert("Please enter a valid amount (minimum KES 50)", "error")
    return
  }

  formData.append("amount", amount)
  formData.append("payment_method", paymentMethod)

  if (paymentMethod === "M-Pesa" || paymentMethod === "Airtel Money") {
    const phoneNumber = document.getElementById("phone_number").value.trim()

    if (!/^(\+254|254|0)(7|1)\d{8}$/.test(phoneNumber)) {
      showAlert("Please enter a valid Kenyan mobile number", "error")
      return
    }

    const pin = window.prompt(`Enter your ${paymentMethod} PIN to confirm payment`)
    if (!pin) {
      showAlert("Payment cancelled. PIN is required.", "error")
      return
    }

    if (!/^\d{4,6}$/.test(pin)) {
      showAlert("Please enter a valid PIN number", "error")
      return
    }

    formData.append("phone_number", phoneNumber)
    formData.append("pin", pin)
  }

  if (paymentMethod === "Bank Transfer") {
    const bankName = document.getElementById("bank_name").value
    const accountHolder = document.getElementById("account_holder").value.trim()
    const accountNumber = document.getElementById("account_number").value.trim()
    const nationalId = document.getElementById("national_id").value.trim()

    if (!bankName || !accountHolder || !accountNumber || !nationalId) {
      showAlert("Please fill in all bank payment details", "error")
      return
    }

    if (!/^[A-Za-z\s.'-]{3,}$/.test(accountHolder)) {
      showAlert("Please enter the account holder's full name", "error")
      return
    }

    if (!/^[A-Za-z0-9-]{5,20}$/.test(accountNumber)) {
      showAlert("Please enter a valid bank account number", "error")
      return
    }

    formData.append("bank_name", bankName)
    formData.append("account_holder", accountHolder)
    formData.append("account_number", accountNumber)
    formData.append("national_id", nationalId)
  }

  if (paymentMethod === "PayPal") {
    const paypalEmail = document.getElementById("paypal_email").value.trim()

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(paypalEmail)) {
      showAlert("Please enter a valid PayPal email address", "error")
      return
    }

    formData.append("paypal_email", paypalEmail)
  }

  showLoading()

  fetch(`/make_payment/${username}`, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading()
      if (data.success) {
        showAlert(`Payment successful! New balance: KES ${data.new_balance}`, "success")
        location.reload()
      } else {
        showAlert(data.error || "Payment failed", "error")
      }
    })
    .catch((error) => {
      hideLoading()
      showAlert("Network error occurred", "error")
      console.error("Error:", error)
    })
}

// Utility functions
function showLoading() {
  const loading = document.querySelector(".loading")
  if (loading) {
    loading.style.display = "block"
  }
}

function hideLoading() {
  const loading = document.querySelector(".loading")
  if (loading) {
    loading.style.display = "none"
  }
}

function showAlert(message, type) {
  const alertDiv = document.createElement("div")
  alertDiv.className = `alert alert-${type}`
  alertDiv.textContent = message

  const container = document.querySelector(".container")
  if (container) {
    container.insertBefore(alertDiv, container.firstChild)

    setTimeout(() => {
      alertDiv.style.opacity = "0"
      setTimeout(() => {
        alertDiv.remove()
      }, 300)
    }, 5000)
  }
}

// Form validation
function validateForm(formId) {
  const form = document.getElementById(formId)
  const inputs = form.querySelectorAll("input[required], select[required]")
  let isValid = true

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      input.style.borderColor = "#dc3545"
      isValid = false
    } else {
      input.style.borderColor = "#ddd"
    }
  })

  return isValid
}

// Print function
function printPass() {
  window.print()
}

// Download QR Code
function downloadQR(qrPath, filename) {
  const link = document.createElement("a")
  link.href = qrPath
  link.download = filename || "bus_pass_qr.png"
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Slideshow functionality
let slideIndex = 0
let slideInterval

function initializeSlideshow() {
  const slides = document.querySelectorAll(".slide")
  const dots = document.querySelectorAll(".dot")

  if (slides.length === 0) return // No slideshow on this page

  // Show first slide
  showSlide(0)

  // Start auto-advance
  startSlideshow()
}

function showSlide(index) {
  const slides = document.querySelectorAll(".slide")
  const dots = document.querySelectorAll(".dot")

  // Hide all slides
  slides.forEach((slide) => slide.classList.remove("active"))
  dots.forEach((dot) => dot.classList.remove("active"))

  // Show current slide
  if (slides[index]) {
    slides[index].classList.add("active")
    if (dots[index]) {
      dots[index].classList.add("active")
    }
  }

  slideIndex = index
}

function nextSlide() {
  const slides = document.querySelectorAll(".slide")
  slideIndex = (slideIndex + 1) % slides.length
  showSlide(slideIndex)
}

function prevSlide() {
  const slides = document.querySelectorAll(".slide")
  slideIndex = (slideIndex - 1 + slides.length) % slides.length
  showSlide(slideIndex)
}

function currentSlide(index) {
  showSlide(index)
  // Restart auto-advance
  stopSlideshow()
  startSlideshow()
}

function startSlideshow() {
  slideInterval = setInterval(nextSlide, 3000) // Change slide every 3 seconds
}

function stopSlideshow() {
  if (slideInterval) {
    clearInterval(slideInterval)
  }
}

// Pause slideshow on hover
document.addEventListener("DOMContentLoaded", () => {
  const slideshowContainer = document.querySelector(".slideshow-container")
  if (slideshowContainer) {
    slideshowContainer.addEventListener("mouseenter", stopSlideshow)
    slideshowContainer.addEventListener("mouseleave", startSlideshow)
  }
})

// Map functionality with correct Eldoret coordinates
const L = window.L // Declare the L variable before using it
function initializeMap() {
  // Initialize Leaflet map centered on Eldoret, Kenya
  window.map = L.map("map").setView([0.5143, 35.2697], 12) // Eldoret coordinates with closer zoom

  // Add OpenStreetMap tiles
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(window.map)

  // Define locations with correct coordinates for Eldoret area
  const locations = [
    {
      name: "Moi University Main Campus",
      coords: [0.5143, 35.2697], // Actual Moi University coordinates
      description: "Main campus and central hub for student transportation",
    },
    {
      name: "Eldoret Town Center",
      coords: [0.52, 35.2697], // Eldoret town center
      description: "City center and main business district",
    },
    {
      name: "Kesses Market",
      coords: [0.45, 35.28], // Kesses area
      description: "Residential area with shopping centers and markets",
    },
    {
      name: "Moi University Annex Campus",
      coords: [0.51, 35.26], // Annex campus location
      description: "University annex campus and student facilities",
    },
    {
      name: "Cheptiret Shopping Center",
      coords: [0.48, 35.3], // Cheptiret area
      description: "Suburban residential area and community centers",
    },
  ]

  // Add clickable markers for each location
  locations.forEach((location) => {
    const marker = L.marker(location.coords).addTo(window.map)

    // Make markers clickable with popup
    marker.bindPopup(`
      <div style="text-align: center;">
        <h4>${location.name}</h4>
        <p>${location.description}</p>
        <small>📍 ${location.coords[0].toFixed(4)}°N, ${location.coords[1].toFixed(4)}°E</small>
      </div>
    `)

    // Add click event to marker
    marker.on("click", function () {
      window.map.setView(location.coords, 15)
      this.openPopup()
    })
  })
}

// Function to zoom to location on map (called from location cards)
function zoomToLocation(lat, lng, name) {
  if (typeof L !== "undefined" && window.map) {
    window.map.setView([lat, lng], 15)

    // Find and open the popup for this location
    window.map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        const markerLatLng = layer.getLatLng()
        if (Math.abs(markerLatLng.lat - lat) < 0.001 && Math.abs(markerLatLng.lng - lng) < 0.001) {
          layer.openPopup()
        }
      }
    })

    showAlert(`Zoomed to ${name}`, "success")
  } else {
    // Fallback to Google Maps
    const url = `https://www.google.com/maps?q=${lat},${lng}`
    window.open(url, "_blank")
  }
}
