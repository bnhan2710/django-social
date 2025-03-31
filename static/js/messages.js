{
    let input_message = $('#input-message')
    let send_message_form = $('#send-message-form')
    let CUR_USER_ID = $('#logged-in-user').val()
    let loc = window.location
    let wsStart = 'ws://'

    if (loc.protocol === 'https:') {
    wsStart = 'wss://'
    }
    let endpoint = wsStart + loc.host + loc.pathname

    var socket = new WebSocket(endpoint)
    $('.chat-messages').animate({
        scrollTop: $('.chat-messages').prop("scrollHeight")
    }, 100)
    socket.onopen = function (e) {
        console.log('open', e)
        send_message_form.on('submit', function(e){
            e.preventDefault()
            let message = input_message.val()
            let send_to = get_active_receiver_id()
            let thread_id = get_active_thread_id()
            let data = {
                'message': message,
                'from': CUR_USER_ID,
                'to': send_to,
                'thread_id': thread_id
            }
            data = JSON.stringify(data)
            console.log(data)
            socket.send(data)
            $(this)[0].reset()
        })
    }
    socket.onmessage = function (e) {
        console.log('message', e)
        let data = JSON.parse(e.data)
        let message = data.message
        let sent_from = data.sent_from
        let thread_id = data.thread_id
        newMessage(message, sent_from, thread_id)
    }
    socket.onerror = function (e) {
        console.log('error', e)
    }
    socket.onclose = function (e) {
        console.log('close', e)
    }

    function get_active_receiver_id(){
        let receiver_id = $('#receiver').attr('receiver-id')
        receiver_id = $.trim(receiver_id)
        return receiver_id
    }
    function get_active_thread_id(){
        let thread_id = $('#receiver').attr('thread-id')
        thread_id = $.trim(thread_id)
        return thread_id
    }
}