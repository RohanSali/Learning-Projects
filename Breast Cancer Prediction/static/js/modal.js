// Modal functionality for prediction results
class PredictionModal {
    constructor() {
        this.modal = null;
        this.overlay = null;
        this.reportData = null;
        this.init();
    }

    init() {
        // Create modal HTML
        this.createModalHTML();
        this.bindEvents();
    }

    createModalHTML() {
        const modalHTML = `
            <div class="modal-overlay" id="predictionModal">
                <div class="modal">
                    <div class="modal-header">
                        <h2>🔬 Clinical Diagnosis Report</h2>
                        <button class="close-btn" onclick="predictionModal.close()">&times;</button>
                    </div>
                    <div class="modal-body" id="modalBody">
                        <!-- Content will be dynamically inserted here -->
                    </div>
                    <div class="modal-footer">
                        <button class="modal-btn download-btn" onclick="predictionModal.downloadReport()">📥 Download Report</button>
                        <button class="modal-btn" onclick="predictionModal.close()">Close Report</button>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        this.modal = document.getElementById('predictionModal');
        this.overlay = this.modal; // Fix: The modal itself is the overlay
    }

    bindEvents() {
        // Close modal when clicking overlay
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) {
                this.close();
            }
        });
    }

    show(result, confidence, usedFeatures, features, randomId) {
        console.log('Modal.show called with:', { result, confidence, usedFeatures, features, randomId });
        
        // Store report data for download functionality
        this.reportData = { result, confidence, usedFeatures, features, randomId };
        
        const modalBody = document.getElementById('modalBody');
        
        // Determine result class and icon
        const resultClass = result === 'Malignant' ? 'result-malignant' : 'result-benign';
        const resultIcon = result === 'Malignant' ? '⚠️' : '✅';
        
        // Get current date for the report
        const currentDate = new Date();
        const formattedDate = currentDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        const formattedTime = currentDate.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Create professional medical report content
        const resultContent = `
            <div class="medical-report">
                <div class="report-header">
                    <div class="report-title">BREAST CANCER DIAGNOSTIC REPORT</div>
                    <div class="report-metadata">
                        <div>Case ID: ${randomId}</div>
                        <div>Report Date: ${formattedDate}</div>
                        <div>Report Time: ${formattedTime}</div>
                    </div>
                </div>
                
                <div class="report-section">
                    <h4>DIAGNOSTIC SUMMARY</h4>
                    <div class="diagnosis-result ${resultClass}">
                        <div class="diagnosis-label">Primary Diagnosis:</div>
                        <div class="diagnosis-value">${resultIcon} ${result} Breast Tissue</div>
                    </div>
                    <div class="diagnosis-confidence">
                        <div class="diagnosis-label">Diagnostic Confidence:</div>
                        <div class="diagnosis-value">${confidence}</div>
                    </div>
                </div>
                
                <div class="report-section">
                    <h4>CLINICAL INTERPRETATION</h4>
                    <p class="clinical-interpretation">
                        ${result === 'Malignant' ? 
                            'The analysis indicates characteristics consistent with <strong>malignant breast tissue</strong>. ' +
                            'This suggests a high probability of cancerous cells based on the cellular features analyzed. ' +
                            'Further clinical correlation and follow-up is strongly recommended.' :
                            'The analysis indicates characteristics consistent with <strong>benign breast tissue</strong>. ' +
                            'The cellular features analyzed suggest non-cancerous tissue. ' +
                            'Regular follow-up as per standard protocols is advised.'}
                    </p>
                </div>
                
                <div class="report-section">
                    <h4>DIAGNOSTIC PARAMETERS</h4>
                    <div class="parameters-grid">
                        ${this.generateParametersHTML(usedFeatures, features)}
                    </div>
                </div>
                
                <div class="report-section">
                    <h4>RECOMMENDATIONS</h4>
                    <ul class="recommendations-list">
                        ${result === 'Malignant' ? `
                            <li>Immediate consultation with an oncologist is recommended</li>
                            <li>Consider additional imaging studies (MRI, ultrasound)</li>
                            <li>Tissue biopsy confirmation if not already performed</li>
                            <li>Develop comprehensive treatment plan</li>
                        ` : `
                            <li>Continue regular breast cancer screening as recommended for patient's age group</li>
                            <li>Follow-up examination in 6 months</li>
                            <li>Report any changes in breast tissue immediately</li>
                            <li>Maintain healthy lifestyle practices</li>
                        `}
                    </ul>
                </div>
                
                <div class="report-footer">
                    <p>This report was generated using an AI-assisted diagnostic system and should be interpreted by a qualified healthcare professional. The results should be correlated with clinical findings and other diagnostic tests.</p>
                </div>
            </div>
        `;
        
        console.log('Modal content to be inserted:', resultContent);
        modalBody.innerHTML = resultContent;
        
        // Show modal with animation
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus management for accessibility
        setTimeout(() => {
            this.modal.querySelector('.close-btn').focus();
        }, 100);
    }

    generateParametersHTML(usedFeatures, features) {
        console.log('Generating parameters HTML with:', { usedFeatures, features });
        
        let html = '';
        
        // Group parameters by category
        const meanFeatures = {};
        const seFeatures = {};
        const worstFeatures = {};
        
        Object.keys(usedFeatures).forEach(feature => {
            if (feature.includes('mean')) {
                meanFeatures[feature] = usedFeatures[feature];
            } else if (feature.includes('_se')) {
                seFeatures[feature] = usedFeatures[feature];
            } else if (feature.includes('worst')) {
                worstFeatures[feature] = usedFeatures[feature];
            }
        });
        
        console.log('Grouped features:', { meanFeatures, seFeatures, worstFeatures });
        
        // Generate HTML for each category
        const categories = [
            { title: 'Mean Values', features: meanFeatures },
            { title: 'Standard Error Values', features: seFeatures },
            { title: 'Worst Values', features: worstFeatures }
        ];
        
        categories.forEach(category => {
            if (Object.keys(category.features).length > 0) {
                html += `<div style="grid-column: 1 / -1; margin-bottom: 20px;">
                    <h5 style="color: #1a237e; margin-bottom: 10px; font-size: 1.1rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px;">
                        ${category.title}
                    </h5>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                `;
                
                Object.keys(category.features).forEach(feature => {
                    const value = category.features[feature];
                    const displayName = features[feature] || feature;
                    html += `
                        <div class="parameter-item">
                            <div class="parameter-name">${displayName}</div>
                            <div class="parameter-value">${value.toFixed(4)}</div>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
            }
        });
        
        console.log('Generated parameters HTML:', html);
        return html;
    }

    downloadReport() {
        if (!this.reportData) {
            console.error('No report data available for download');
            return;
        }

        const { result, confidence, usedFeatures, features, randomId } = this.reportData;
        
        // Get current date for the report
        const currentDate = new Date();
        const formattedDate = currentDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        const formattedTime = currentDate.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Create a filename with case ID and date
        const filename = `breast_cancer_report_${randomId}_${formattedDate.replace(/\s/g, '_')}.html`;
        
        // Create the report content
        const reportContent = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Breast Cancer Diagnostic Report - Case ${randomId}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .report-header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #ddd;
                }
                .report-title {
                    font-size: 24px;
                    font-weight: bold;
                    color: #1a237e;
                    margin-bottom: 15px;
                }
                .report-metadata {
                    display: flex;
                    justify-content: space-around;
                    color: #666;
                    font-size: 14px;
                }
                .report-section {
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #eee;
                }
                h4 {
                    color: #1a237e;
                    font-size: 18px;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #eee;
                }
                .diagnosis-result {
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                    color: white;
                    font-weight: bold;
                    display: flex;
                    justify-content: space-between;
                }
                .result-malignant {
                    background-color: #ff6b6b;
                }
                .result-benign {
                    background-color: #2ecc71;
                }
                .diagnosis-confidence {
                    padding: 15px;
                    background-color: #f1f8e9;
                    border-radius: 5px;
                    margin-bottom: 15px;
                    color: #33691e;
                    display: flex;
                    justify-content: space-between;
                }
                .clinical-interpretation {
                    line-height: 1.7;
                    color: #37474f;
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                    border-left: 4px solid #3f51b5;
                }
                .parameters-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }
                .parameter-category {
                    margin-bottom: 20px;
                }
                .parameter-category h5 {
                    color: #1a237e;
                    margin-bottom: 10px;
                    font-size: 16px;
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 5px;
                }
                .parameter-item {
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #e0e0e0;
                    margin-bottom: 10px;
                }
                .parameter-name {
                    font-weight: bold;
                    color: #37474f;
                    font-size: 14px;
                    margin-bottom: 5px;
                }
                .parameter-value {
                    color: #2196f3;
                    font-weight: bold;
                    font-size: 16px;
                }
                .recommendations-list {
                    list-style-type: none;
                    padding: 0;
                }
                .recommendations-list li {
                    padding: 10px 15px;
                    margin-bottom: 10px;
                    background: #e8f5e9;
                    border-radius: 5px;
                    color: #2e7d32;
                    position: relative;
                    padding-left: 30px;
                }
                .recommendations-list li:before {
                    content: '✓';
                    position: absolute;
                    left: 10px;
                    color: #2e7d32;
                    font-weight: bold;
                }
                .report-footer {
                    font-size: 12px;
                    color: #78909c;
                    font-style: italic;
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                }
                @media print {
                    body {
                        padding: 0;
                        font-size: 12pt;
                    }
                    .no-print {
                        display: none;
                    }
                }
            </style>
        </head>
        <body>
            <div class="report-header">
                <div class="report-title">BREAST CANCER DIAGNOSTIC REPORT</div>
                <div class="report-metadata">
                    <div>Case ID: ${randomId}</div>
                    <div>Report Date: ${formattedDate}</div>
                    <div>Report Time: ${formattedTime}</div>
                </div>
            </div>
            
            <div class="report-section">
                <h4>DIAGNOSTIC SUMMARY</h4>
                <div class="diagnosis-result ${result === 'Malignant' ? 'result-malignant' : 'result-benign'}">
                    <div>Primary Diagnosis:</div>
                    <div>${result === 'Malignant' ? '⚠️' : '✅'} ${result} Breast Tissue</div>
                </div>
                <div class="diagnosis-confidence">
                    <div>Diagnostic Confidence:</div>
                    <div>${confidence}</div>
                </div>
            </div>
            
            <div class="report-section">
                <h4>CLINICAL INTERPRETATION</h4>
                <p class="clinical-interpretation">
                    ${result === 'Malignant' ? 
                        'The analysis indicates characteristics consistent with <strong>malignant breast tissue</strong>. ' +
                        'This suggests a high probability of cancerous cells based on the cellular features analyzed. ' +
                        'Further clinical correlation and follow-up is strongly recommended.' :
                        'The analysis indicates characteristics consistent with <strong>benign breast tissue</strong>. ' +
                        'The cellular features analyzed suggest non-cancerous tissue. ' +
                        'Regular follow-up as per standard protocols is advised.'}
                </p>
            </div>
            
            <div class="report-section">
                <h4>DIAGNOSTIC PARAMETERS</h4>
                ${this.generateParametersHTMLForDownload(usedFeatures, features)}
            </div>
            
            <div class="report-section">
                <h4>RECOMMENDATIONS</h4>
                <ul class="recommendations-list">
                    ${result === 'Malignant' ? `
                        <li>Immediate consultation with an oncologist is recommended</li>
                        <li>Consider additional imaging studies (MRI, ultrasound)</li>
                        <li>Tissue biopsy confirmation if not already performed</li>
                        <li>Develop comprehensive treatment plan</li>
                    ` : `
                        <li>Continue regular breast cancer screening as recommended for patient's age group</li>
                        <li>Follow-up examination in 6 months</li>
                        <li>Report any changes in breast tissue immediately</li>
                        <li>Maintain healthy lifestyle practices</li>
                    `}
                </ul>
            </div>
            
            <div class="report-footer">
                <p>This report was generated using an AI-assisted diagnostic system and should be interpreted by a qualified healthcare professional. The results should be correlated with clinical findings and other diagnostic tests.</p>
                <p class="no-print">Generated on ${formattedDate} at ${formattedTime}</p>
            </div>
            
            <div class="no-print" style="text-align: center; margin-top: 30px;">
                <button onclick="window.print()" style="padding: 10px 20px; background: #3f51b5; color: white; border: none; border-radius: 5px; cursor: pointer;">Print Report</button>
            </div>
        </body>
        </html>
        `;
        
        // Create a Blob with the HTML content
        const blob = new Blob([reportContent], { type: 'text/html' });
        
        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = filename;
        
        // Trigger the download
        document.body.appendChild(downloadLink);
        downloadLink.click();
        
        // Clean up
        document.body.removeChild(downloadLink);
        URL.revokeObjectURL(downloadLink.href);
    }

    generateParametersHTMLForDownload(usedFeatures, features) {
        let html = '<div class="parameters-grid">';
        
        // Group parameters by category
        const meanFeatures = {};
        const seFeatures = {};
        const worstFeatures = {};
        
        Object.keys(usedFeatures).forEach(feature => {
            if (feature.includes('mean')) {
                meanFeatures[feature] = usedFeatures[feature];
            } else if (feature.includes('_se')) {
                seFeatures[feature] = usedFeatures[feature];
            } else if (feature.includes('worst')) {
                worstFeatures[feature] = usedFeatures[feature];
            }
        });
        
        // Generate HTML for each category
        const categories = [
            { title: 'Mean Values', features: meanFeatures },
            { title: 'Standard Error Values', features: seFeatures },
            { title: 'Worst Values', features: worstFeatures }
        ];
        
        categories.forEach(category => {
            if (Object.keys(category.features).length > 0) {
                html += `<div class="parameter-category">
                    <h5>${category.title}</h5>
                    <div class="parameters-grid">
                `;
                
                Object.keys(category.features).forEach(feature => {
                    const value = category.features[feature];
                    const displayName = features[feature] || feature;
                    html += `
                        <div class="parameter-item">
                            <div class="parameter-name">${displayName}</div>
                            <div class="parameter-value">${value.toFixed(4)}</div>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
            }
        });
        
        html += '</div>';
        return html;
    }

    close() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        
        // Focus management
        setTimeout(() => {
            const submitBtn = document.querySelector('.submit-btn');
            if (submitBtn) {
                submitBtn.focus();
            }
        }, 300);
    }

    isOpen() {
        return this.modal.classList.contains('active');
    }
}

// Initialize modal
const predictionModal = new PredictionModal();

// Form submission handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up form handler');
    
    const form = document.querySelector('form');
    const submitBtn = document.querySelector('.submit-btn');
    
    if (form) {
        console.log('Form found, adding submit handler');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            // Show loading state
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="loading"></span> Analyzing...';
            submitBtn.disabled = true;
            
            // Submit form via AJAX
            const formData = new FormData(form);
            console.log('Form data:', Object.fromEntries(formData));
            
            fetch('/predict', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('Response received:', response);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                
                if (data.error) {
                    console.error('Server error:', data.error);
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Ensure we have the required data
                if (!data.result) {
                    console.error('No result in response:', data);
                    alert('Error: No diagnosis result received');
                    return;
                }
                
                console.log('Calling modal.show with:', {
                    result: data.result,
                    confidence: data.confidence,
                    usedFeatures: data.used_features,
                    features: window.featureNames,
                    randomId: data.random_id
                });
                
                // Show modal with results
                predictionModal.show(
                    data.result, 
                    data.confidence, 
                    data.used_features, 
                    window.featureNames || {},
                    data.random_id
                );
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request. Please try again.');
            })
            .finally(() => {
                // Restore button state
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    } else {
        console.error('Form not found!');
    }
});

// Add feature names to window for modal access
window.featureNames = {
    'radius_mean': 'Radius Mean',
    'texture_mean': 'Texture Mean', 
    'perimeter_mean': 'Perimeter Mean',
    'area_mean': 'Area Mean',
    'smoothness_mean': 'Smoothness Mean',
    'compactness_mean': 'Compactness Mean',
    'concavity_mean': 'Concavity Mean',
    'concave points_mean': 'Concave Points Mean',
    'symmetry_mean': 'Symmetry Mean',
    'fractal_dimension_mean': 'Fractal Dimension Mean',
    'radius_se': 'Radius SE',
    'texture_se': 'Texture SE',
    'perimeter_se': 'Perimeter SE',
    'area_se': 'Area SE',
    'smoothness_se': 'Smoothness SE',
    'compactness_se': 'Compactness SE',
    'concavity_se': 'Concavity SE',
    'concave points_se': 'Concave Points SE',
    'symmetry_se': 'Symmetry SE',
    'fractal_dimension_se': 'Fractal Dimension SE',
    'radius_worst': 'Radius Worst',
    'texture_worst': 'Texture Worst',
    'perimeter_worst': 'Perimeter Worst',
    'area_worst': 'Area Worst',
    'smoothness_worst': 'Smoothness Worst',
    'compactness_worst': 'Compactness Worst',
    'concavity_worst': 'Concavity Worst',
    'concave points_worst': 'Concave Points Worst',
    'symmetry_worst': 'Symmetry Worst',
    'fractal_dimension_worst': 'Fractal Dimension Worst'
};