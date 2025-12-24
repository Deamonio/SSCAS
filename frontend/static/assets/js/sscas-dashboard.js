/**
 * SSCAS Dashboard JavaScript Module
 * Handles image polling and data fetching
 */

class SSCASClient {
    constructor() {
        this.pollingIntervals = {
            image: 3000,      // 3 seconds for images
            character: 2000    // 2 seconds for character data
        };
        this.endpoints = {
            image1: '/get_image/1',
            image2: '/get_image/2',
            character: '/get_character',
            poll: '/poll_characters'
        };
    }

    /**
     * Poll for image updates
     * @param {string} imageId - ID of the image element
     * @param {string} endpoint - API endpoint
     * @param {number} interval - Polling interval in ms
     */
    pollImage(imageId, endpoint, interval) {
        const imageElement = document.getElementById(imageId);
        if (!imageElement) {
            console.error(`Image element ${imageId} not found`);
            return;
        }

        const fetchImage = async () => {
            try {
                const response = await fetch(endpoint);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                
                // Release old object URL to prevent memory leaks
                if (imageElement.src && imageElement.src.startsWith('blob:')) {
                    URL.revokeObjectURL(imageElement.src);
                }
                
                imageElement.src = imageUrl;
            } catch (error) {
                console.error(`Error polling image ${imageId}:`, error);
            } finally {
                setTimeout(fetchImage, interval);
            }
        };

        fetchImage();
    }

    /**
     * Fetch and display character/analysis data
     */
    async fetchCharacter() {
        try {
            const response = await fetch(this.endpoints.character);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.updateCharacterDisplay(data);
        } catch (error) {
            console.error('Error fetching character data:', error);
        }
    }

    /**
     * Update character data display
     * @param {Object} data - Character data from server
     */
    updateCharacterDisplay(data) {
        const fields = ['place', 'time', 'person', 'density'];
        
        fields.forEach(field => {
            const element = document.getElementById(field);
            if (element) {
                const label = field.charAt(0).toUpperCase() + field.slice(1);
                element.innerHTML = `<strong>${label}:</strong> ${data[field] || 'N/A'}`;
            }
        });
    }

    /**
     * Start long polling for character updates
     */
    startCharacterPolling() {
        const pollCharacters = async () => {
            try {
                const response = await fetch(this.endpoints.poll);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Check if we have new data
                if (data.place || data.time || data.person || data.density) {
                    this.updateCharacterDisplay(data);
                }
            } catch (error) {
                console.error('Error polling characters:', error);
            } finally {
                setTimeout(pollCharacters, this.pollingIntervals.character);
            }
        };

        pollCharacters();
    }

    /**
     * Initialize the dashboard
     */
    initialize() {
        // Start image polling
        this.pollImage('image', this.endpoints.image1, this.pollingIntervals.image);
        this.pollImage('heatmap', this.endpoints.image2, 1000);
        
        // Fetch initial character data
        this.fetchCharacter();
        
        // Start character polling
        this.startCharacterPolling();
        
        console.log('SSCAS Dashboard initialized');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const client = new SSCASClient();
    client.initialize();
});
