// store the currently selected tab in the hash value
$("#nav-tab a").on("shown.bs.tab", function (e) {
    let id = $(e.target).attr("href");
    window.sessionStorage.setItem('last-tab', id)
});

// on load of the page: switch to the currently selected tab
$(`#nav-tab a[href="${window.sessionStorage.getItem('last-tab')}"]`).tab('show');

let sortable = new Sortable(document.querySelector("#links-list"), {
    handle: ".lbt-draggable",
    animation: 200,
    store: {
        get: function (sortable) {
            let order = String($('#links-list').data('links-order'));
            console.log(order);
            order = order ? order.split('|') : [];
            return order;
        },
        set: function (sortable) {
            const list = $('#links-list');
            let order = sortable.toArray();
            const token = list.data('csrf')
            $.ajax({
                type: "POST",
                url: list.data('path'),
                data: JSON.stringify({order}),
                dataType: 'json',
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': token
                },
            })
        },
    },
})
