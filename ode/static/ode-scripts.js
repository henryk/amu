function replace_with_select2(element_id)
{
    $('#' + element_id).replaceWith(function(){
        var result = $("<select id='"+element_id+"' multiple='multiple'/>");
        result.attr('class', $(this).attr('class'));
        return result;
    });
}

$(function(){
    $('.table tr[data-href]').each(function(){
        $(this).css('cursor','pointer').hover(
            function(){ 
                $(this).addClass('active'); 
            },  
            function(){ 
                $(this).removeClass('active'); 
            }).click( function(){ 
                document.location = $(this).attr('data-href'); 
            }
        );
    });
});

$(function() {
    if($("*[autofocus]").length == 0) {
        var mod = $("form *.has-error input").first().attr('autofocus', 'autofocus').focus();
        if(mod.length == 0) {
            $('form input:text[value=""]:visible:enabled:first').first().attr('autofocus', 'autofocus').focus();
        }
    }
});
