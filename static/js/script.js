$("form[name=signup-form").submit(function (e) {

    var form = this;
    var data = new FormData(form)

    $.ajax({
        url: "/user/signup",
        type: "POST",
        data: data,
        dataType: "json",
        processData: false,
        contentType: false,
        success: function (resp) {
            if (resp.redirect){
                window.location.href = resp.redirect;
            }
        },
        error: function (resp) {
            const errorDiv = document.getElementById("alert-div");
            errorDiv.textContent = resp.responseJSON.error || "Signup Failed";
            errorDiv.classList.add("alert-error");
        }
    });

    e.preventDefault();

});

$("form[name=otp-verification-form]").submit(function (e) {

    var form = this;
    var data = new FormData(form)

    $.ajax({
        url: "/user/verify-otp",
        type: "POST",
        data: data,
        dataType: "json",
        processData: false,
        contentType: false,
        success: function (resp) {
            if (resp.redirect){
                window.location.href = resp.redirect;
            }
        },
        error: function (resp) {
            const errorDiv = document.getElementById("alert-div");
            errorDiv.textContent = resp.responseJSON.error || "Signup Failed";
            errorDiv.classList.add("alert-error");
        }
    });

    e.preventDefault();
 
});

$("form[name=login-form").submit(function (e) {

    var $form = $(this);
    var data = $form.serialize();

    $.ajax({
        url: "/user/login",
        type: "POST",
        data: data,
        dataType: "json",
        success: function (resp) {
            console.log(resp);
            alert("Login Successful! Welcome back to TripSync Community! Redirecting to Dashboard...");
            window.location.href = "/dashboard";
        },
        error: function (resp) {
            console.log(resp);
            alert(resp.responseJSON.error);
        }
    });

    e.preventDefault();

});

$("form[name=host-trip-form").submit(function (e) {
    var form = this;
    var data = new FormData(form)

    $.ajax({
        url: "/trip/host",
        type: "POST",
        data: data,
        dataType: "json",
        processData: false,
        contentType: false,
        success: function (resp) {
            console.log(resp);
            alert("Trip Creation Successful! Redirecting to Dashboard...");
            window.location.href = "/dashboard";
        },
        error: function (resp) {
            console.log(resp);
            alert(resp.responseJSON.error);
        }
    });

    e.preventDefault();
});