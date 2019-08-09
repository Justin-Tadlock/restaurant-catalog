window.onload = function() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/authenticated');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        var response = JSON.parse(xhr.responseText);

        if (response.status == 201) {
            console.log("User logged in");
            showSignInBtn(false);            
        }
        else if (response.status == 202) {
            console.log("User not logged in");
            showSignInBtn(true);            
        }
    }
    xhr.send();
}



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
        showSignInBtn(true);

        loc = window.location.href

        if (loc.search('edit') > 0 || loc.search('add') > 0 || loc.search('delete') > 0) {
            window.location.href = '/'
        }
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
                showSignInBtn(false);
            }
        };
        xhr.send('idtoken=' + id_token);
    }
}