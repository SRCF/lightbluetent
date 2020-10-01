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

    /* Show the recurring options if they're selected on page load */
    var recurring_checkbox = document.getElementById("recurring_checkbox")
    if (recurring_checkbox.checked) {
        $("#recurring_box").show();
    } else {
        $("#recurring_box").hide();
    }

    /* Enable the alias input if selected on page load */
    var alias_checkbox = document.getElementById("alias_checkbox")
    var alias_input = document.getElementById("alias_input")
    if (alias_checkbox.checked) {
        alias_input.disabled = false;
    } else {
        alias_input.disabled = true;
    }

    $('.limit_option').hide();
    var value = $('#limit_select').val();
    if (value == "until") {
        $('#limit_box_until').show();
    } else if (value == "number") {
        $('#limit_box_number').show();
    }

    /* Show the correct div if the values change */
    $('input[type="radio"]').change(function() {
    	var auth_type = $(this).val();
        $("div.auth-box").hide();
        $("#auth_box_"+auth_type).show();
    });


    $('input[type="checkbox"]').click(function() {

        /* Enable or disable the alias box */
        var alias_input = document.getElementById("alias_input");
        if (this.id == "alias_checkbox") {
            if ($(this).is(":checked")) {
                alias_input.disabled = false;
            } else {
                alias_input.disabled = true;
            }
        }

        /* Show or hide the recurrence settings */
        if (this.id == "recurring_checkbox") {
            if ($(this).is(":checked")) {
                $("#recurring_box").show();
            } else {
                $("#recurring_box").hide();
            }
        }
    });

    /* Show or hide the limit settings */
    $('#limit_select').change(function() {
        $('.limit_option').hide();
        var value = $(this).val();
        if (value == "until") {
            $('#limit_box_until').show();
        } else if (value == "number") {
            $('#limit_box_number').show();
        }
    });

});

