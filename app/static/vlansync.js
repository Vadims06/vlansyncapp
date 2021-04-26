function js_delete_selected_vlans() {
    var array = []
    var checkboxes = document.querySelectorAll('input[type=checkbox]:checked')
  
    for (var i = 0; i < checkboxes.length; i++) {
      array.push(checkboxes[i].value)
    }
    $.ajax({
      url: "/delete_selected_vlans",
      type: "post",
      data: {'selected_vlans_ll_json': JSON.stringify(array)}
    })
  }

function show_instant_notification(message) {
    $( '#popUpInstantMessageID').text(message);
    $( '#popUpInstantMessageID').show().delay(4500).fadeOut(2000);
}