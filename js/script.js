$(document).ready(function(){
  function form_select(key, value, min, max)
  {
    var html = '';

    html = html + '<label for="' + key + '">' + key + '</label> ';
    html = html + '<select name="' + key + '" id="' + key + '">';
    for (var i = min; i <= max; i++){
      var hex = i.toString(16);
      if (i < 16) hex = '0' + hex;
      if (max >= 256 && i < 256) hex = '0' + hex;
      if (max >= 256 && i < 4096) hex = '0' + hex;
      html = html + '<option value="' + hex + '"';
      if (hex == value) html = html + ' selected';
      html = html + '>' + hex + ' (' + i + ')</option>';
    }

    html = html + '</select>';
    html = html + ' (' + value + ')';

    return html;
  }

  function loading() {
    // Loading...
    var el = $('#lights h4');
    el.html(el.html() + '.');
    setTimeout(function(){
      el.html(el.html() + '.');
    },1000);
  }

  function draw(data)
  {
    var settings = { power: {min: 0, max: 1}, sec_count: {min: 1, max: 2048}, dot_count: {min: 1, max: 300}, pattern: {min: 0, max: 255}, brightness: {min: 0, max: 255}, speed: {min: 0, max: 255}, red: {min: 0, max: 255}, green: {min: 0, max: 255}, blue: {min: 0, max: 255} };
    var html = '';
    for (var i in data.messages) {
        html = html + '<p>' + data.messages[i] + '</p>'
    }
    html = html + '<form>';
    for (var key in settings) {
        var setting = settings[key];
        var value = data.settings[key];
        html = html + form_select(key, value, setting.min, setting.max) + "<br/>\n";
    }
    html = html + '<button type="submit">Update</button>';
    html = html + '</form>';
    $('#lights').html(html);
  }

  function update()
  {
    loading();
    $.getJSON('/cgi-bin/lights.cgi', function(data) {
      draw(data);
    });
  }

  update();

  $('body').on('click', 'button', function(e) {
    e.preventDefault();
    var args = {}; $('select').each(function(){ var key = $(this).attr('name'); args[key] = $(this).val(); });
    $('#lights').html('<h4>Updating.</h4>');
    loading();
    $.getJSON('/cgi-bin/lights.cgi', {state:JSON.stringify(args)}, function(data) {
      draw(data);
    }).fail(function(){
      $('#lights').html('<h4>Update failed. Loading.</h4>');
      update();
    });
  });
});
