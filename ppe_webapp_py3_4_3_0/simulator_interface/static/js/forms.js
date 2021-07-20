var form_elements = document.querySelectorAll('.form-field');
form_elements.forEach(
  item => {
    form_content = item.innerHTML
    form_args = form_content.split(" ")
    form_args.splice(2, 0, "class='form-control' ");
    item.innerHTML = form_args.join(" ")
  }
);
