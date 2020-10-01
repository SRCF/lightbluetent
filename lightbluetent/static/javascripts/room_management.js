$(document).ready(function() {

    /* Show the password div if that's selected on page load */
    if ($("input[name='authentication']:checked").val() == "password") {
        $("div.auth-box").hide();
        $("#auth_box_password").show();
    }

    /* Show the whitelist div if that's selected on page load */
    if ($("input[name='authentication']:checked").val() == "whitelist") {
        $("div.auth-box").hide();
        $("#auth_box_whitelist").show();
    }

    /* Show the correct div if the values change */
    $('input[type="radio"]').change(function() {
    	var auth_type = $(this).val();
        $("div.auth-box").hide();
        $("#auth_box_"+auth_type).show();
    });

    /* Enable or disable the alias box */
    $('input[type="checkbox"]').click(function() {

        var input = document.getElementById("alias_input");

        if($(this).is(":checked")) {
            input.disabled = false;
        } else {
            input.disabled = true;
        }

    });


});


