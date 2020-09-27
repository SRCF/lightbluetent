// change site setting from dropdown
function changeSiteSetting(paths, data, token) {
    $.ajax({
        type: "POST",
        url: paths.success,
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': token
        },
    }).done(function() {
        window.location.reload();
    }).fail(function(res, status, error) {
        $.ajax({
            type: "POST",
            url: paths.error,
            data: JSON.stringify({ code: res.status, name: error }),
            dataType: 'json',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': token
            }
        }).done(function(){
            window.location.reload();
        })
    });
}

// change whether signups should be enabled
$('#enable-signups .dropdown-menu').on('click', '> *', function () {
    const paths = {
        success: $('#enable-signups').data('path'), error: $('#enable-signups').data('path-error')
    };
    const data = { name: "enable_signups", enabled: $(this).data('action') == "enable" }
    const token = $('#enable-signups').data('csrf');
    changeSiteSetting(paths, data, token)
});