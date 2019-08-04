function showSignInBtn(setVisible) {
    if(setVisible) {
        $('.sign-in').css('display', 'block');
        $('.sign-out').css('display', 'none');
    }
    else {
        $('.sign-in').css('display', 'none');
        $('.sign-out').css('display', 'block');
    }
}

function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
    console.log('User signed out.');
    });

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/oauthcallback');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        console.log('Logging out the user.');

        $.ajax({
            type:'GET',
            url:'/',
            success: function() {
                window.location.href = '/';
            }
        }) 

        showSignInBtn(true);
    }
    xhr.send('logout=true');
    
}

function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.

    if (profile != null) {
        var id_token = googleUser.getAuthResponse().id_token;

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/oauthcallback');
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onload = function() {
            response = JSON.parse(xhr.responseText);

            if (response['status'] == 200) {
                $.ajax({
                    type:'GET',
                    url:'/',
                    success: function() {
                        result_text = response['message'] + " Reloading in 4 seconds...";
                        $('.result').html(result_text);
                        setTimeout(function() {
                            window.location.href="/";
                        }, 4000);
                    }
                })
            }

            showSignInBtn(false);
        };
        xhr.send('idtoken=' + id_token);
    }
}