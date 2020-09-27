// change site setting from dropdown
function changeSiteSetting(path, data, token) {
    $.ajax({
        type: "POST",
        url: path,
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': token
        },
    }).done(function () {
        window.location.reload();
    })
}

// change whether signups should be enabled
$('#enable-signups .dropdown-menu').on('click', '> *', function () {
    const path = $('#enable-signups').data('path');
    const data = { name: "enable_signups", enabled: $(this).data('action') == "enable" }
    const token = $('#enable-signups').data('csrf');
    changeSiteSetting(path, data, token)
});

