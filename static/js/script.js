// Webcam Face Detection Functionality
function initWebcamDetection() {
    const startCameraBtn = document.getElementById('startCamera');
    const stopCameraBtn = document.getElementById('stopCamera');
    const webcamFeed = document.getElementById('webcamFeed');
    const webcamPlaceholder = document.getElementById('webcamPlaceholder');
    const faceCountElement = document.getElementById('faceCount');
    const detectionStatus = document.getElementById('detectionStatus');
    const cameraStatus = document.getElementById('cameraStatus');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const resultsPanel = document.getElementById('resultsPanel');
    const facesList = document.getElementById('facesList');
    const scaleFactor = document.getElementById('scaleFactor');
    const minNeighbors = document.getElementById('minNeighbors');
    const scaleValue = document.getElementById('scaleValue');
    const neighborsValue = document.getElementById('neighborsValue');
    const loadingModal = document.getElementById('loadingModal');
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');

    let isCameraRunning = false;
    let faceCountInterval = null;

    // Update range values
    scaleFactor.addEventListener('input', updateScaleValue);
    minNeighbors.addEventListener('input', updateNeighborsValue);

    function updateScaleValue() {
        const value = parseFloat(scaleFactor.value);
        if (value <= 1.1) scaleValue.textContent = 'Low';
        else if (value <= 1.2) scaleValue.textContent = 'Medium';
        else scaleValue.textContent = 'High';
    }

    function updateNeighborsValue() {
        const value = parseInt(minNeighbors.value);
        if (value <= 4) neighborsValue.textContent = 'Fast';
        else if (value <= 6) neighborsValue.textContent = 'Balanced';
        else neighborsValue.textContent = 'Accurate';
    }

    // Initialize values
    updateScaleValue();
    updateNeighborsValue();

    // Start Camera
    startCameraBtn.addEventListener('click', startCamera);

    // Stop Camera
    stopCameraBtn.addEventListener('click', stopCamera);

    async function startCamera() {
        try {
            showLoadingModal();
            
            const response = await fetch('/start_camera', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            hideLoadingModal();

            if (data.success) {
                isCameraRunning = true;
                updateUIForRunningState();
                
                // Show webcam feed with a small delay to ensure stream is ready
                setTimeout(() => {
                    webcamFeed.style.display = 'block';
                    webcamPlaceholder.style.display = 'none';
                    resultsPanel.style.display = 'block';
                    
                    // Force refresh the video feed
                    webcamFeed.src = webcamFeed.src + '?t=' + new Date().getTime();
                }, 1000);

                // Start face count polling
                startFaceCountPolling();
                
                showNotification('Camera started successfully! Face detection is now active.', 'success');
            } else {
                showErrorModal('Failed to start camera: ' + data.message);
            }
        } catch (error) {
            hideLoadingModal();
            showErrorModal('Error starting camera: ' + error.message);
        }
    }

    function stopCamera() {
        fetch('/stop_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                isCameraRunning = false;
                updateUIForStoppedState();
                
                // Stop face count polling
                if (faceCountInterval) {
                    clearInterval(faceCountInterval);
                    faceCountInterval = null;
                }
                
                showNotification('Camera stopped successfully.', 'success');
            } else {
                showNotification('Failed to stop camera: ' + data.message, 'error');
            }
        })
        .catch(error => {
            showNotification('Error stopping camera: ' + error.message, 'error');
        });
    }

    function updateUIForRunningState() {
        startCameraBtn.disabled = true;
        stopCameraBtn.disabled = false;
        statusDot.classList.add('active');
        statusText.textContent = 'Camera Active';
        cameraStatus.textContent = 'Online';
        detectionStatus.textContent = 'Monitoring';
        startCameraBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Starting...';
        
        // Reset button text after a delay
        setTimeout(() => {
            startCameraBtn.innerHTML = '<i class="fas fa-play"></i> Camera Running';
        }, 2000);
    }

    function updateUIForStoppedState() {
        startCameraBtn.disabled = false;
        stopCameraBtn.disabled = true;
        statusDot.classList.remove('active');
        statusText.textContent = 'Camera Offline';
        cameraStatus.textContent = 'Offline';
        detectionStatus.textContent = 'Inactive';
        faceCountElement.textContent = '0';
        webcamFeed.style.display = 'none';
        webcamPlaceholder.style.display = 'flex';
        resultsPanel.style.display = 'none';
        facesList.innerHTML = '<div class="face-item"><div class="face-info"><span>No faces detected</span></div></div>';
        startCameraBtn.innerHTML = '<i class="fas fa-play"></i> Start Camera';
    }

    function startFaceCountPolling() {
        // Clear existing interval
        if (faceCountInterval) {
            clearInterval(faceCountInterval);
        }

        // Poll for face count every second
        faceCountInterval = setInterval(async () => {
            try {
                const response = await fetch('/get_face_count');
                const data = await response.json();
                
                if (data.success) {
                    faceCountElement.textContent = data.face_count;
                    updateFacesList(data.face_count);
                    
                    // Update detection status based on face count
                    if (data.face_count > 0) {
                        detectionStatus.textContent = `${data.face_count} Face${data.face_count > 1 ? 's' : ''} Detected`;
                        detectionStatus.style.color = '#28a745';
                    } else {
                        detectionStatus.textContent = 'Monitoring';
                        detectionStatus.style.color = '';
                    }
                }
            } catch (error) {
                console.error('Error fetching face count:', error);
            }
        }, 1000);
    }

    function updateFacesList(faceCount) {
        facesList.innerHTML = '';
        
        if (faceCount > 0) {
            for (let i = 1; i <= faceCount; i++) {
                const faceItem = document.createElement('div');
                faceItem.className = 'face-item';
                faceItem.innerHTML = `
                    <div class="face-info">
                        <strong>Face #${i}</strong>
                        <span>Detected in frame</span>
                    </div>
                    <div class="face-confidence" style="color: #28a745;">● Live</div>
                `;
                facesList.appendChild(faceItem);
            }
        } else {
            const noFacesItem = document.createElement('div');
            noFacesItem.className = 'face-item';
            noFacesItem.innerHTML = `
                <div class="face-info">
                    <span>No faces detected</span>
                </div>
                <div class="face-confidence" style="color: #dc3545;">● None</div>
            `;
            facesList.appendChild(noFacesItem);
        }
    }

    function showLoadingModal() {
        loadingModal.style.display = 'flex';
    }

    function hideLoadingModal() {
        loadingModal.style.display = 'none';
    }

    function showErrorModal(message) {
        errorMessage.textContent = message;
        errorModal.style.display = 'flex';
    }

    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
            <span>${message}</span>
        `;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    // Check camera status on page load
    checkCameraStatus();

    async function checkCameraStatus() {
        try {
            const response = await fetch('/api/camera_status');
            const data = await response.json();
            
            if (data.camera_active) {
                isCameraRunning = true;
                updateUIForRunningState();
                webcamFeed.style.display = 'block';
                webcamPlaceholder.style.display = 'none';
                resultsPanel.style.display = 'block';
                startFaceCountPolling();
            }
        } catch (error) {
            console.log('Camera status check failed:', error);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Navigation toggle for mobile
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
        });
    }

    // Initialize webcam detection if on detection page
    if (document.querySelector('.webcam-container')) {
        initWebcamDetection();
    }

    // Initialize contact form
    if (document.getElementById('contactForm')) {
        initContactForm();
    }
});

// Contact Form Functionality
function initContactForm() {
    const contactForm = document.getElementById('contactForm');
    
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Simple form validation
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const subject = document.getElementById('subject').value;
        const message = document.getElementById('message').value;
        
        if (!name || !email || !subject || !message) {
            alert('Please fill in all fields.');
            return;
        }
        
        // Simulate form submission
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        
        // In a real application, you would send this to your backend
        setTimeout(() => {
            alert('Thank you for your message! We will get back to you soon.');
            contactForm.reset();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }, 2000);
    });
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);