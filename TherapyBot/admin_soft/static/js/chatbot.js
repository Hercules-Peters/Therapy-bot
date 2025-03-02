document.addEventListener("DOMContentLoaded", () => {
    const chatBody = document.querySelector(".chat-body")
    const chatForm = document.querySelector(".chat-form")
    const messageInput = document.querySelector(".message-input")
    const fileInput = document.querySelector("#file-input")
    const fileUploadWrapper = document.querySelector(".file-upload-wrapper")
    const fileCancelButton = document.querySelector("#file-cancel")
    const fileUploadButton = document.querySelector("#file-upload")
    const sendButton = document.querySelector("#send-message")
    const emojiPickerButton = document.querySelector("#emoji-picker")

    // Create message element with dynamic classes and return it
    const createMessageElement = (content, isUser = false, attachment = null) => {
        const div = document.createElement("div")
        div.classList.add("message", isUser ? "user-message" : "bot-message")

        if (!isUser) {
            div.innerHTML = `
                <svg class="bot-avatar" xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 1024 1024">
                    <path d="M738.3 287.6H285.7c-59 0-106.8 47.8-106.8 106.8v303.1c0 59 47.8 106.8 106.8 106.8h81.5v111.1c0 .7.8 1.1 1.4.7l166.9-110.6 41.8-.8h117.4l43.6-.4c59 0 106.8-47.8 106.8-106.8V394.5c0-59-47.8-106.9-106.8-106.9zM351.7 448.2c0-29.5 23.9-53.5 53.5-53.5s53.5 23.9 53.5 53.5-23.9 53.5-53.5 53.5-53.5-23.9-53.5-53.5zm157.9 267.1c-67.8 0-123.8-47.5-132.3-109h264.6c-8.6 61.5-64.5 109-132.3 109zm110-213.7c-29.5 0-53.5-23.9-53.5-53.5s23.9-53.5 53.5-53.5 53.5 23.9 53.5 53.5-23.9 53.5-53.5 53.5zM867.2 644.5V453.1h26.5c19.4 0 35.1 15.7 35.1 35.1v121.1c0 19.4-15.7 35.1-35.1 35.1h-26.5zM95.2 609.4V488.2c0-19.4 15.7-35.1 35.1-35.1h26.5v191.3h-26.5c-19.4 0-35.1-15.7-35.1-35.1zM561.5 149.6c0 23.4-15.6 43.3-36.9 49.7v44.9h-30v-44.9c-21.4-6.5-36.9-26.3-36.9-49.7 0-28.6 23.3-51.9 51.9-51.9s51.9 23.3 51.9 51.9z"/>
                </svg>`
        }

        const messageText = document.createElement("div")
        messageText.className = "message-text"
        messageText.textContent = content
        div.appendChild(messageText)

        if (attachment) {
            const img = document.createElement("img")
            img.src = attachment
            img.className = "attachment"
            div.appendChild(img)
        }

        return div
    }

    // Add thinking indicator while waiting for response
    const addThinkingIndicator = () => {
        const thinkingDiv = document.createElement("div")
        thinkingDiv.className = "message bot-message thinking"
        thinkingDiv.innerHTML = `
                <svg class="bot-avatar" xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 1024 1024">
                    <path d="M738.3 287.6H285.7c-59 0-106.8 47.8-106.8 106.8v303.1c0 59 47.8 106.8 106.8 106.8h81.5v111.1c0 .7.8 1.1 1.4.7l166.9-110.6 41.8-.8h117.4l43.6-.4c59 0 106.8-47.8 106.8-106.8V394.5c0-59-47.8-106.9-106.8-106.9zM351.7 448.2c0-29.5 23.9-53.5 53.5-53.5s53.5 23.9 53.5 53.5-23.9 53.5-53.5 53.5-53.5-23.9-53.5-53.5zm157.9 267.1c-67.8 0-123.8-47.5-132.3-109h264.6c-8.6 61.5-64.5 109-132.3 109zm110-213.7c-29.5 0-53.5-23.9-53.5-53.5s23.9-53.5 53.5-53.5 53.5 23.9 53.5 53.5-23.9 53.5-53.5 53.5zM867.2 644.5V453.1h26.5c19.4 0 35.1 15.7 35.1 35.1v121.1c0 19.4-15.7 35.1-35.1 35.1h-26.5zM95.2 609.4V488.2c0-19.4 15.7-35.1 35.1-35.1h26.5v191.3h-26.5c-19.4 0-35.1-15.7-35.1-35.1zM561.5 149.6c0 23.4-15.6 43.3-36.9 49.7v44.9h-30v-44.9c-21.4-6.5-36.9-26.3-36.9-49.7 0-28.6 23.3-51.9 51.9-51.9s51.9 23.3 51.9 51.9z"/>
                </svg>
                <div class="message-text">
                    <div class="thinking-indicator">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                </div>`
        chatBody.appendChild(thinkingDiv)
        chatBody.scrollTop = chatBody.scrollHeight
        return thinkingDiv
    }

    // Handle message submission
    const handleSubmit = async (e) => {
        e.preventDefault()
        const message = messageInput.value.trim()
        if (!message && !fileInput.files[0]) return

        let attachment = null
        const formData = new FormData()
        formData.append("message", message)

        if (fileInput.files[0]) {
            const file = fileInput.files[0]
            formData.append("file", file)
            attachment = URL.createObjectURL(file) // Update: Use URL.createObjectURL
        }

        // Add user message to chat
        const userMessageDiv = createMessageElement(message, true, attachment)
        chatBody.appendChild(userMessageDiv)
        messageInput.value = ""

        // Reset file upload if any
        if (fileUploadWrapper.classList.contains("file-uploaded")) {
            fileUploadWrapper.classList.remove("file-uploaded")
            fileUploadWrapper.querySelector("img").src = "#"
            fileInput.value = ""
        }

        // Add thinking indicator
        const thinkingIndicator = addThinkingIndicator()

        try {
            const response = await fetch("/chat/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
            })

            const data = await response.json()

            // Remove thinking indicator
            thinkingIndicator.remove()

            if (data.error) {
                throw new Error(data.error)
            }

            // Add bot response
            const botMessageDiv = createMessageElement(data.response, false)
            chatBody.appendChild(botMessageDiv)
        } catch (error) {
            console.error("Error:", error)
            thinkingIndicator.remove()
            const errorMessageDiv = createMessageElement(
                error.message === "API quota exceeded. Please try again later."
                    ? "The service is currently busy. Please try again in a few minutes."
                    : "Sorry, something went wrong. Please try again.",
                false,
            )
            chatBody.appendChild(errorMessageDiv)
        }

        chatBody.scrollTop = chatBody.scrollHeight
    }

    // Handle file selection
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0]
        if (!file) return

        const reader = new FileReader()
        reader.onload = (e) => {
            fileUploadWrapper.querySelector("img").src = e.target.result
            fileUploadWrapper.classList.add("file-uploaded")
        }
        reader.readAsDataURL(file)
    })

    // Handle file upload cancel
    fileCancelButton.addEventListener("click", () => {
        fileInput.value = ""
        fileUploadWrapper.classList.remove("file-uploaded")
        fileUploadWrapper.querySelector("img").src = "#"
    })

    // Handle form submission
    chatForm.addEventListener("submit", handleSubmit)

    // Handle file upload button click
    fileUploadButton.addEventListener("click", () => fileInput.click())

    // Handle Enter key press to send message
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            chatForm.dispatchEvent(new Event("submit", { cancelable: true }))
        }
    })

    // Initialize emoji picker
    let emojiPickerVisible = false
    // Import EmojiMart here.  This assumes it's available via a script tag or a module import.
    const picker = new EmojiMart.Picker({
        onEmojiSelect: (emoji) => {
            const start = messageInput.selectionStart
            const end = messageInput.selectionEnd
            messageInput.value = messageInput.value.substring(0, start) + emoji.native + messageInput.value.substring(end)
            messageInput.focus()
            document.body.classList.remove("show-emoji-picker")
            emojiPickerVisible = false
        },
    })

    // Handle emoji picker toggle
    emojiPickerButton.addEventListener("click", () => {
        if (!emojiPickerVisible) {
            document.body.classList.add("show-emoji-picker")
            if (!document.querySelector("emoji-picker-container")) {
                const container = document.createElement("emoji-picker-container")
                container.appendChild(picker)
                document.querySelector(".chat-form").appendChild(container)
            }
        } else {
            document.body.classList.remove("show-emoji-picker")
        }
        emojiPickerVisible = !emojiPickerVisible
    })

    // Close emoji picker when clicking outside
    document.addEventListener("click", (e) => {
        if (emojiPickerVisible && !e.target.closest("emoji-picker-container") && e.target.id !== "emoji-picker") {
            document.body.classList.remove("show-emoji-picker")
            emojiPickerVisible = false
        }
    })

    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";")
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim()
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                    break
                }
            }
        }
        return cookieValue
    }
})

