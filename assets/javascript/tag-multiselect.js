'use strict'
import htmx from 'htmx.org'
import TomSelect from "tom-select";

const urlData = document.getElementById('tag-multiselect');
const linkTagUrl = urlData.getAttribute("data-linkTagUrl");
const unlinkTagUrl = urlData.getAttribute("data-unlinkTagUrl");

let controlInstances = [];

function addTag (name, objectInfo) {
  return function () {
    let postData = {swap: 'none', values: {"tag_name": arguments[0], "object_info": objectInfo}};
    htmx.ajax('POST', linkTagUrl, postData);
    let dropdown_option = {text: arguments[0], value: arguments[0]};
    // Add the new tag to all existing TomSelect instances. This will do nothing if it already exists
    controlInstances.forEach((controlInstance) => {
      controlInstance.addOption(dropdown_option);
    });
  };
}

function removeTag (name, objectInfo) {
  return function () {
    let postData = {swap: 'none', values: {"tag_name": arguments[0], "object_info": objectInfo}};
    htmx.ajax('POST', unlinkTagUrl, postData);
  };
}

function configureTomSelect() {
  const filter = '.tag-multiselect:not(.tomselected):not(.ts-wrapper)';
  document.querySelectorAll(filter).forEach((el) => {
    let objectInfo = el.getAttribute("data-info");
    let control = new TomSelect(el, {
      maxItems: null,
      create: true,
      onItemAdd: addTag('onItemAdd', objectInfo),
      onItemRemove: removeTag('onItemRemove', objectInfo)
    });
    controlInstances.push(control);
  });
}

export const setupTagSelects = () => {
  configureTomSelect();
  htmx.on("htmx:afterSwap", () => { configureTomSelect() });
}
