(function($){


    // Function to convert timestamps to human time. eg. 1 minute ago
    function updatePostTimes() {
        var now = moment.utc(new Date());

        $('.post-time').each(function(idx, src) {
            var parsedTime = moment.utc($(src).data('datetime'));

            $(src).html(parsedTime.fromNow())
        });
    }


    // Post back when the like button is clicked
    $('.like-btn').click(function(btn) {
        btn.preventDefault();

        $.ajax({
            type: "POST",
            url: '/post/like',
            data: {
                post_ref: $(btn.currentTarget).data('post')
            },
            success: function(data, status) {
                if (data.redirect) {
                    window.location = data.redirect;
                } else {
                    window.location.reload();
                }
            }
        });
    });


    // Show Modal confirmation modal. On delete will redirect, else reload page.
    $("#deleteModal").on('click', '.btn-danger', function(e) {
        e.preventDefault();

        var deleteBtn = $(this);

        $.ajax({
            type: "POST",
            url: '/' + deleteBtn.data('type') + '/delete',
            data: {
                id: deleteBtn.data('id')
            },
            success: function(data) {
                if (data.redirect) {
                    window.location = data.redirect;
                } else {
                    window.location.reload();
                }
            }
        });
    });


    // Set data on modal before being shown
    $("#deleteModal").on('show.bs.modal', function(e) {
        var data = $(e.relatedTarget).data();
        var modal = $(this);

        modal.find("span.content-type").html( data.type );
        modal.find('button.btn-danger')
            .data('type', data.type)
            .data('id', data.id);
    });


    $("#submitCmtBtn").on("click", function(e) {
        e.preventDefault();

        if ( $("#comment").val().length >= 10 ) {
            $(e.target).closest("form").submit();
        } else {
            $("#cmtError").html("<p class='text-danger'>Enter at least 10 characters</p>");
        }
    });


    // Show Modal edit comment modal.
    $("#editCommentModal").on('click', '.btn-danger', function(e) {
        e.preventDefault();

        var saveBtn = $(this);
        var modalBody = saveBtn.parent().prev();
        var currentText = modalBody.find("textarea").val();
        var errorP = modalBody.children("p");

        if ( currentText.length >= 10 ) {
            $.ajax({
                type: "POST",
                url: "/comment/update",
                data: {
                    id: saveBtn.data("id"),
                    comment: currentText
                },
                success: function(data) {
                    if (data.redirect) {
                        window.location = data.redirect;
                    } else {
                        window.location.reload();
                    }
                }
            });
        } else {
            errorP.html('Comments need to be at least 10 character.');
        }
    });


    // Set data on modal before being shown
    $("#editCommentModal").on('show.bs.modal', function(e) {
        var relatedTarget = $(e.relatedTarget);
        var modalData = relatedTarget.data();
        var modal = $(this);

        // Set the textarea to the comment data
        modal.find("textarea").val( relatedTarget.parent()
                                                    .prev()
                                                    .find(".comment-body")
                                                    .text() );

        modal.find('button.btn-danger')
             .data('id', modalData.id);
    });


    // Init run to update timestamps
    updatePostTimes();

    // Runs momentjs every minute to update timestamps on the page
    setInterval(updatePostTimes, 60*1000);
})(jQuery);
