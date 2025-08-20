<template>
  <v-app>
    <!-- Header -->
    <v-app-bar :color="theme.global.name.value === 'light' ? 'primary' : 'grey-darken-3'" app>
      <v-btn icon variant="plain" :ripple="false" href="http://localhost:5173/">
        <img
          src="/res/images/logo.svg"
          style="width: 40px; height: 40px"
        >
      </v-btn>
      
      <v-toolbar-title>Sapphire File Server</v-toolbar-title>
      
      <div class="d-flex justify-space-between align-center ga-2 pa-3">
        <v-btn :icon="theme.global.name.value === 'dark' ? 'mdi-moon-waxing-crescent' : 'mdi-white-balance-sunny'"
        @click="switchTheme()"
        ></v-btn>
        <span>Signed in as:</span>
        <v-btn prepend-icon="mdi-account-circle" rounded="xl" stacked circle>
          admin
        </v-btn>
      </div>

      <v-progress-linear :active="isZipping || isLoading" indeterminate rounded="pill" location="bottom" absolute></v-progress-linear>
    </v-app-bar>

    <!-- Sidebar + Content -->
    <v-navigation-drawer app v-model="drawer">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      
      <v-divider></v-divider>

      <v-list :lines="false" density="compact" nav>
        <v-list-item
          v-for="(item, i) in navigationDrawerMenus"
          :key="i"
          :value="item"
          :active="item.page === currentPage"
          @click="currentPage = item.page"
          color="primary"
        >
          <template v-slot:prepend>
            <v-icon :icon="item.icon"></v-icon>
          </template>
          <v-list-item-title v-text="item.text"></v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container style="height: 100%;" @click.self="selectedItems = []">
        <div v-shortkey="['ctrl', 'a']" @shortkey="isRenaming || isDeleting ? 0 : selectAll()" style="display: none"></div>
        <div v-shortkey="['ctrl', 'i']" @shortkey="isRenaming || isDeleting ? 0 : invertSelection()" style="display: none"></div>
        <div v-shortkey="['esc']" @shortkey="cancelOperation()" style="display: none"></div>
        <div v-shortkey="['arrowdown']" @shortkey="isRenaming || isDeleting ? 0 : moveSelection(1)" style="display: none"></div>
        <div v-shortkey="['shift', 'arrowdown']" @shortkey="isRenaming || isDeleting ? 0 : moveSelection(1)" style="display: none"></div>
        <div v-shortkey="['arrowup']" @shortkey="isRenaming || isDeleting ? 0 : moveSelection(-1)" style="display: none"></div>
        <div v-shortkey="['shift', 'arrowup']" @shortkey="isRenaming || isDeleting ? 0 : moveSelection(-1)" style="display: none"></div>
        <v-list v-if="currentPage === Pages.MyFiles" class="pa-4" style="user-select: none;" rounded="xl">
          <div class="d-flex justify-center ps-4">
          </div>
          <v-breadcrumbs>
            <v-btn width="30" height="30" icon="mdi-home" size="small" variant="text" tabindex="-1" @click="setCurrentPath('')">
            </v-btn>
            <v-breadcrumbs-divider v-if="currentPath !== ''"></v-breadcrumbs-divider>
            <div v-for="pathPart in getPathParts()">
              <v-btn height="30" class="text-none" variant="text" rounded="pill" tabindex="-1" style="padding: 0 8px;" @click="setCurrentPath(pathPart)">
                {{ getPathLastFolder(pathPart) }}
              </v-btn>
              <v-breadcrumbs-divider></v-breadcrumbs-divider>
            </div>
          </v-breadcrumbs>
          <v-divider></v-divider>
          <div class="d-flex justify-space-between">
            <div class="d-flex justify-start pa-3">
              <v-btn class="text-none" prepend-icon="mdi-arrow-left-top" variant="text" rounded="pill" tabindex="-1"
              :disabled="currentPath === ''" @click="goBackDirectory()">
                Go back
              </v-btn>
              <v-tooltip text="Refresh" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" height="36" width="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  v-shortkey="['ctrl', 'r']" @shortkey="updateItems()" @click="updateItems()">
                    <v-icon size="20">mdi-refresh</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
            </div>
            <div class="d-flex justify-start pa-3">
              <v-btn class="text-none" prepend-icon="mdi-folder-plus" variant="text" rounded="pill" tabindex="-1"
              @click="createNewFolder()" v-shortkey="['ctrl', 'shift', 'n']" @shortkey="createNewFolder()">
                New Folder
              </v-btn>
              <v-btn class="text-none" prepend-icon="mdi-file-plus" variant="text" rounded="pill" tabindex="-1"
              @click="createNewFile()" v-shortkey="['alt', 'n']" @shortkey="createNewFile()">
                New File
              </v-btn>
            </div>
            <div class="d-flex justify-start ga-3 pa-3">
              <v-tooltip text="Cut" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" height="36" width="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  v-shortkey="['ctrl', 'x']" @shortkey="selectedItems.length !== 0 ? cutSelected() : 0"
                  @click="cutSelected()" :disabled="selectedItems.length === 0">
                    <v-icon size="20">mdi-content-cut</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Copy" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" width="36" height="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  v-shortkey="['ctrl', 'c']" @shortkey="selectedItems.length !== 0 ? copySelected() : 0"
                  @click="copySelected()" :disabled="selectedItems.length === 0">
                    <v-icon size="20">mdi-content-copy</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Paste" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" width="36" height="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  v-shortkey="['ctrl', 'v']" @shortkey="clipboard.length !== 0 ? pasteSelected() : 0"
                  @click="pasteSelected()" :disabled="clipboard.length === 0">
                    <v-icon size="20">mdi-content-paste</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Rename" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" width="36" height="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  v-shortkey="['f2']" @shortkey="selectedItems.length === 1 ? promptNewName() : 0"
                  @click="promptNewName()" :disabled="selectedItems.length !== 1">
                    <v-icon size="20">mdi-form-textbox</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Delete" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" width="36" height="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  v-shortkey="['del']" @shortkey="selectedItems.length !== 0 ? promptDelete() : 0"
                  @click="promptDelete()" :disabled="selectedItems.length === 0">
                    <v-icon size="20">mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Export" location="bottom" transition="fade-transition" open-delay="750">
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" width="36" height="36" icon="" variant="text" rounded="pill" tabindex="-1"
                  @click="promptShare()" :disabled="selectedItems.length === 0">
                    <v-icon size="20">mdi-export-variant</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
            </div>
            <div class="d-flex justify-start pa-3">
              <v-btn class="text-none" prepend-icon="mdi-download" variant="text" rounded="pill" tabindex="-1"
              :disabled="selectedItems.length === 0" @click="downloadSelectedFiles()">
                Download
              </v-btn>
              <v-btn class="text-none" prepend-icon="mdi-upload" variant="text" rounded="pill" tabindex="-1">
                Upload
              </v-btn>
            </div>
          </div>
          <v-divider></v-divider>
          <v-list-item>
            <div class="d-flex justify-space-between mt-2">
              <v-btn
                class="text-none"
                variant="text"
                rounded="pill" 
                tabindex="-1"
                @click="
                delayedChangeSorting(SortingModes.Name);
                "
              >
                File Name
                <v-icon>
                  {{ getSortingIcon(SortingModes.Name) }}
                </v-icon>
              </v-btn>
              <v-btn
                class="text-none"
                variant="text"
                rounded="pill"
                tabindex="-1"
                @click="
                delayedChangeSorting(SortingModes.Type);
                "
              >
                Type
                <v-icon>
                  {{ getSortingIcon(SortingModes.Type) }}
                </v-icon>
              </v-btn>
              <v-btn
                class="text-none"
                variant="text"
                rounded="pill"
                tabindex="-1"
                @click="
                delayedChangeSorting(SortingModes.Size);
                "
              >
                Size
                <v-icon>
                  {{ getSortingIcon(SortingModes.Size) }}
                </v-icon>
              </v-btn>
              <v-btn
                class="text-none"
                variant="text"
                rounded="pill"
                tabindex="-1"
                @click="
                delayedChangeSorting(SortingModes.LastModified);
                "
              >
                Last Modified
                <v-icon>
                  {{ getSortingIcon(SortingModes.LastModified) }}
                </v-icon>
              </v-btn>
            </div>
          </v-list-item>
          <v-banner
          v-if="networkError"
          class="justify-center text-deep-orange"
          >
            <v-icon class="mr-3" size="large">
              mdi-alert
            </v-icon>
            <v-banner-text>
              Couldn't reach server. This could be because the server is offline or due to bad internet connection.
            </v-banner-text>
          </v-banner>
          <v-list-item
            v-else
            v-for="(file, index) in sortedItems"
            :key="index"
            :value="file"
            :active="includesFile(selectedItems, file)"
            :disabled="itemsBeingCut.includes(currentPath + file.name)"
            :ref="el => {itemRefs[file.name] = el}"
            tabindex="-1"
            color="primary"
            :style="{
              borderRadius: getItemBorderRadius(file) + ' !important',
              transition: 'border-radius 0.2s ease-in-out'
            }"
            @click="isLoading ? 0 : delayedToggleFileSelected(file)"
            @dblclick="isLoading ? 0 : changePath(file)"
          >
            <div style="display: flex; width: 100%; align-items: center;">
              <div style="flex: 2; display: flex; align-items: center; gap: 8px;">
                <v-icon :icon="getFileIcon(file)"></v-icon>
                {{ file.name }}
              </div>

              <div style="flex: 1;">
                {{ getItemTypeDescription(file) }}
              </div>

              <div style="flex: 1;">
                {{ getFileSize(file) }}
              </div>

              <div style="flex: 1; justify-self: right;">
                {{ getItemLastModifiedDate(file) }}
              </div>
            </div>
          </v-list-item>
        </v-list>
        <div class="pa-3" style="position: fixed; bottom: 0; right: 0px;">
          <p>
            {{ `${selectedItems.length} / ${sortedItems.length} items selected` }}
          </p>
        </div>
      </v-container>
      <v-dialog v-model="isRenaming" max-width="500">
        <v-card class="ps-2 pt-6 pb-6" rounded="xl" title="Enter a new name">
          <v-text-field class="ml-10 mr-10" variant="outlined" v-model="itemNewName" autofocus label="New Name"
          :placeholder="itemNewName" persistent-placeholder type="input"
          v-shortkey="['enter']" @shortkey="isRenaming ? renameSelected() : 0"
          ></v-text-field>
          <v-card-actions>
            <v-btn @click="cancelOperation()">Cancel</v-btn>
            <v-btn autofocus @click="renameSelected()" color="primary">Ok</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="isDeleting" max-width="550">
        <v-card class="pa-6" rounded="xl" :title="`Do you want to delete the following (${selectedItems.length}) items?`"
        v-shortkey="['enter']" @shortkey="isDeleting ? deleteSelected() : 0"
        >
          <v-list class="ps-6">
            <div class="text-none d-flex ps-5 pb-1 pt-2 ga-2" v-for="item in selectedItems">
              <v-icon>
                {{ getFileIcon(item) }}
              </v-icon>
              <p>
                {{ item.name }}
              </p>
            </div>
          </v-list>
          <v-card-actions>
            <v-btn @click="cancelOperation()">Cancel</v-btn>
            <v-btn autofocus @click="deleteSelected()" color="primary">Ok</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, toRaw, onMounted, onBeforeUnmount } from 'vue';
import { useTheme } from 'vuetify';

import VueCookies from 'vue-cookies'

import { getFileIcon, fileExtensionDescriptions } from "./fileIcons.js";

const theme = useTheme()

const keysDown = ref(new Set());

function keyDownCallback(event) {
  keysDown.value.add(event.key);
}

function keyUpCallback(event) {
  keysDown.value.delete(event.key);
}

onMounted(() => {
  checkStoredTheme();
  window.addEventListener('keydown', keyDownCallback);
  window.addEventListener('keyup', keyUpCallback);
  updateItems();
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', keyDownCallback);
  window.removeEventListener('keyup', keyUpCallback);
});

const Pages = {
  MyFiles: 0,
  Recent: 1,
  Prex: 2,
  Backups: 3
};

const currentPage = ref(Pages.MyFiles);

const SortingOrders = {
  Ascending: 1,
  Descending: 2
};

const SortingModes = {
  Name: 0,
  Type: 1,
  Size: 2,
  LastModified: 3
};

const sortingOrder = ref(SortingOrders.Ascending);
const sortingMode = ref(SortingModes.Name);

const filesAndDirectories = ref([]);
const sortedItems = ref([]);
const itemRefs = ref({});
const clipboard = ref([]);
const itemsBeingCut = ref([]);

const isRenaming = ref(false);
const itemNewName = ref("");
const isDeleting = ref(false);

const isZipping = ref(false);
const isLoading = ref(false);
const networkError = ref(false);

function checkStoredTheme() {
  let themeCookie = VueCookies.get("app.themeCookie");
  if (themeCookie) {
    theme.change(themeCookie);
  }
}

function switchTheme() {
  theme.toggle();
  VueCookies.set("app.themeCookie", theme.current(), -1);
}

async function updateItems() {
  try {
    isLoading.value = true;
    const response = await fetch("http://127.0.0.1:8000/files/" + currentPath.value);
    if (!response.ok) {
      setCurrentPath("");
      isLoading.value = false;
      networkError.value = true;
      return;
    }
    const data = await response.json();
    
    networkError.value = false;
    filesAndDirectories.value = data;
    sortedItems.value = sortFiles();
    selectedItems.value = [];
    isLoading.value = false;

  } catch (err) {
    setCurrentPath("");
    isLoading.value = false;
    networkError.value = true;
  }
}

async function openFile(file) {
  fetch("http://127.0.0.1:8000/download/" + currentPath.value + file.name)
  .then(res => res.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  })
  .catch(err => console.error("Error fetching file:", err));
}

async function downloadSelectedFiles() {
  isZipping.value = true;
  selectedItems.value.forEach( (file, i, array) => {
      fetch("http://127.0.0.1:8000/download/" + currentPath.value + file.name)
      .then(res => res.blob())
      .then(blob => {
        const link = document.createElement('a');
        console.log("Creating blob...")
        const url = URL.createObjectURL(blob);
        console.log("Blob created")
        link.href = url;
        link.download = file.name;
        isZipping.value = false;
        link.click();
        URL.revokeObjectURL(url);
      })
    }
  )
}

function changeSorting(newMode) {
  if (sortingMode.value !== newMode) {
    sortingMode.value = newMode;
    sortingOrder.value = SortingOrders.Ascending;
  }
  else {
    sortingOrder.value = sortingOrder.value === SortingOrders.Ascending ? SortingOrders.Descending : SortingOrders.Ascending;
  }

  sortedItems.value = sortFiles();
}

function delayedChangeSorting(newMode) {
  setTimeout(changeSorting, 175, newMode);
}

function getSortingIcon(mode) {
  if (sortingMode.value !== mode) {
    return '';
  }
  switch (sortingOrder.value) {
    case SortingOrders.Ascending: return "mdi-arrow-down";
    case SortingOrders.Descending: return "mdi-arrow-up";
  }
}

function getFileIndex(array, file) {
  return array.findIndex((f) => areItemsSame(f, file));
}

function includesFile(array, file) {
  return getFileIndex(array, file) !== -1;
}

function compareFileNames(nameA, nameB) {
  return nameA.localeCompare(nameB);
}

function getFileScreenPosition(file) {
  const component = itemRefs.value[file.name];
  if (!component) return 0;

  const element = component.$el;

  console.log(element);
  const rect = element.getBoundingClientRect();
  if (rect.bottom < 0) {
    return -1;
  }
  else if (rect.top > window.innerHeight) {
    return 1;
  }
  return 0;
}

function sortFiles() {
  let sortingOrderMultipier = sortingOrder.value === SortingOrders.Ascending ? 1 : -1;

  switch (sortingMode.value) {
    case SortingModes.Name: return [...(filesAndDirectories.value)].sort(
      (a, b) => sortingOrderMultipier * compareFileNames(a.name, b.name)
    ).reduce((result, element) => {
      result[(element.size < 0) ? 0 : 1].push(element);
      return result;
    },
    [[], []]).flat();
    case SortingModes.Type: return [...(filesAndDirectories.value)].sort(
      (a, b) => {
        let fileExtensionA = getItemNameExtension(a.name);
        let fileExtensionB = getItemNameExtension(b.name);
        return sortingOrderMultipier * fileExtensionA.localeCompare(fileExtensionB);
      }
    );
    case SortingModes.Size: return [...(filesAndDirectories.value)].sort(
      (a, b) => sortingOrderMultipier * (a.size - b.size)
    );
    case SortingModes.LastModified: return [...(filesAndDirectories.value)].sort(
      (a, b) => sortingOrderMultipier * (a.lastModified - b.lastModified)
    );
  }
}

let selectedItems = ref([]);

function toggleFileSelected(file) {
  const selectedFileIndex = getFileIndex(selectedItems.value, file);
  if (keysDown.value.has("Control")) {
    if (selectedFileIndex === -1) {
      selectedItems.value.push(file);
    }
    else {
      selectedItems.value.splice(selectedFileIndex, 1);
    }
  }
  else if (keysDown.value.has("Shift") && selectedItems.value.length !== 0) {
    let startIndex = getFileIndex(sortedItems.value, selectedItems.value[0]);
    let endIndex = getFileIndex(sortedItems.value, file);
    
    if (endIndex < startIndex) {
      selectedItems.value = toRaw(sortedItems.value).slice(endIndex, startIndex + 1).reverse();
    }
    else {
      selectedItems.value = toRaw(sortedItems.value).slice(startIndex, endIndex + 1);
    }

  }
  else {
    if (selectedFileIndex === -1) {
      selectedItems.value = [file];
    }
    else {
      selectedItems.value = selectedItems.value.length > 1 ? [file] : [];
    }
  }
}

function delayedToggleFileSelected(file) {
  setTimeout(toggleFileSelected, 150, file);
}

function moveSelection(direction) {
  if (keysDown.value.has("Control")) {
    return;
  }
  let selectionEndIndex = getFileIndex(sortedItems.value, selectedItems.value[selectedItems.value.length - 1]);
  if ((selectionEndIndex === 0 && direction === -1) || (selectionEndIndex === sortedItems.value.length - 1 && direction === 1)) {
    return;
  }
  const newFile = sortedItems.value[selectionEndIndex + direction]
  toggleFileSelected(newFile);
  const fileScreenPosition = getFileScreenPosition(newFile);
  console.log("fileScreenPosition", fileScreenPosition);
  if (fileScreenPosition === 0) {
    return;
  }
  window.scrollBy({
    top:  fileScreenPosition * window.innerHeight * 1.0, // nearly a full page
    behavior: "smooth"
  });
}

function deletePaths(paths) {
  console.log(paths);
  fetch("http://127.0.0.1:8000/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "mode": "delete"
    },
    body: JSON.stringify({
      paths: paths
    })
  }).then(_ => {
    updateItems();
  });
}

function selectAll() {
  selectedItems.value = [...sortedItems.value];
}

function invertSelection() {
  let newSelection = [];
  sortedItems.value.forEach((file) => {
    if (!includesFile(selectedItems.value, file)) {
      newSelection.push(file);
    }
  });
  selectedItems.value = newSelection;
}

function cutSelected() {
  clipboard.value = selectedItems.value.map((file) => currentPath.value + file.name);
  itemsBeingCut.value = [...clipboard.value];
}

function copySelected() {
  clipboard.value = selectedItems.value.map((file) => currentPath.value + file.name);
}

function pasteSelected() {
  const numCopiedItems = selectedItems.value.length;
  let newSelectionNames = [];
  selectedItems.value = [];
  clipboard.value.forEach((path) => {
    fetch("http://127.0.0.1:8000/modify/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "mode": "copy"
      },
      body: JSON.stringify({
        source: path,
        destination: currentPath.value
      })
    }).then(response => {
      if (!response.ok) {
        throw new Error("There was an error while copying an item.");
      }
      return response.json();
    }).then(response => {
      newSelectionNames.push(response.name);
      if (newSelectionNames.length === numCopiedItems) {
        updateItems().then(_ => {
          selectedItems.value = sortedItems.value.filter(file => file.name in newSelectionNames);
          if (itemsBeingCut.value.length !== 0) {
            deletePaths(itemsBeingCut.value);
            itemsBeingCut.value = [];
            clipboard.value = [];
          }
          updateItems();
        });
      }
    });
  });
}

function promptNewName() {
  isRenaming.value = true;
  itemNewName.value = selectedItems.value[0].name;
}

function renameSelected() {
  isRenaming.value = false;
  fetch("http://127.0.0.1:8000/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "mode": "rename",
    },
    body: JSON.stringify({
      path: currentPath.value + selectedItems.value[0].name,
      newName: itemNewName.value
    })
  }).then(response => {
    if (!response.ok) {
      throw new Error("There was an error while renaming the item.");
    }
    return response.json();
  }).then(_ => {
    itemNewName.value = "";
    updateItems();
  });
}

function promptDelete() {
  isDeleting.value = true;
}

function deleteSelected() {
  deletePaths(selectedItems.value.map((file) => currentPath.value + file.name));
  isDeleting.value = false;
}

function createNewFolder() {
  fetch("http://127.0.0.1:8000/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "mode": "newFolder",
    },
    body: JSON.stringify({path: currentPath.value})
  }).then(response => {
    if (!response.ok) {
      throw new Error("There was an error while creating a new folder.");
    }
    return response.json();
  }).then(response => {
    updateItems().then(_ => {
      selectedItems.value = [sortedItems.value[sortedItems.value.findIndex(f => f.name === response.name)]];
      promptNewName();
    });
  });
}

function createNewFile() {
  fetch("http://127.0.0.1:8000/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "mode": "newFile",
    },
    body: JSON.stringify({path: currentPath.value})
  }).then(response => {
    if (!response.ok) {
      throw new Error("There was an error while creating a new file.");
    }
    return response.json();
  }).then(response => {
    updateItems().then(_ => {
      selectedItems.value = [sortedItems.value[sortedItems.value.findIndex(f => f.name === response.name)]];
      promptNewName();
    });
  });
}

function cancelOperation() {
  if (itemsBeingCut.value.length !== 0) {
    itemsBeingCut.value = [];
    clipboard.value = [];
  }
  if (isRenaming.value) {
    isRenaming.value = false;
    itemNewName.value = "";
  }
  if (isDeleting.value) {
    isDeleting.value = false;
  }
}

const navigationDrawerMenus = [
  {text: "My Files", icon: "mdi-folder", page: Pages.MyFiles},
  {text: "Recent", icon: "mdi-history", page: Pages.Recent},
  {text: "Plex", icon: "mdi-cast", page: Pages.Plex},
  {text: "Backups", icon: "mdi-cloud-upload", page: Pages.Backups},
];

const fileSizeUnits = {
  "B":  1,
  "KB": 1_000,
  "MB": 1_000_000,
  "GB": 1_000_000_000,
  "TB": 1_000_000_000_000,
  "PB": 1_000_000_000_000_000
}

function areItemsSame(a, b) {
  return a.name === b.name && a.size === b.size && a.lastModified ===b.lastModified;
}

function getFileSize(file) {
  if (file.size < 0) {
    return "";
  }

  for (const [unit, size] of Object.entries(fileSizeUnits)) {
    let displayedSize = file.size / size;
    if (displayedSize < 1_000) {
      return parseFloat(displayedSize.toFixed(2)).toString() + " " + unit;
    }
  }
}

function getItemLastModifiedDate(file) {
  const date = new Date(file.lastModified * 1000);

  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}\u202F/\u202F${month}\u202F/\u202F${day} \u202F${hour}:${minute}`;

}

function getItemNameExtension(fileName) {
  let i = fileName.lastIndexOf('.');
  if (i === -1) {
    return "";
  }
  return fileName.slice(i + 1);
}

function getItemTypeDescription(file) {
  if (file.size === -1) {
    return "File Folder";
  }

  let fileExtension = getItemNameExtension(file.name);
  if (fileExtension in fileExtensionDescriptions) {
    return fileExtensionDescriptions[fileExtension];
  }
  else {
    return "File";
  }
}

const drawer = ref(true);

const currentPath = ref("");

function changePath(file) {
  if (file.size === -1) {
    currentPath.value += file.name + '/';
    updateItems();
  }
  else {
    openFile(file);
  }
}

function getItemBorderRadius(file) {
  if (selectedItems.value.findIndex(f => areItemsSame(f, file)) === -1) {
    return "25px 25px 25px 25px";
  }

  let i = sortedItems.value.findIndex(f => areItemsSame(f, file));
  let doRoundTop = (i !== 0) ? selectedItems.value.findIndex(f => areItemsSame(f, sortedItems.value[i - 1])) === -1 : true;
  let doRoundBottom = (i !== sortedItems.value.length - 1) ? selectedItems.value.findIndex(f => areItemsSame(f, sortedItems.value[i + 1])) === -1 : true;

  if (doRoundTop && doRoundBottom) {
    return "25px 25px 25px 25px";
  }
  if (doRoundTop) {
    return "25px 25px 0px 0px";
  }
  if (doRoundBottom) {
    return "0px 0px 25px 25px";
  }
  return "0px 0px 0px 0px";
}

function getPathParts() {
  let parts = [];
  let p = currentPath.value;
  while (p !== "") {
    parts.unshift(p);
    p = p.slice(0, p.lastIndexOf('/', p.length - 2) + 1);
  }
  return parts;
}

function getPathLastFolder(path) {
  return path.slice(path.lastIndexOf('/', path.length - 2) + 1, path.length - 1);
}

function setCurrentPath(path) {
  currentPath.value = path;
  updateItems();
}

function goBackDirectory() {
  console.log("before", currentPath.value);
  const pathParts = getPathParts();
  if (pathParts.length === 1) {
    setCurrentPath("");
  }
  else {
    setCurrentPath(pathParts[pathParts.length - 2]);
  }
  console.log("after", currentPath.value);
}

</script>


<script>
export default {
  methods: {
    showAlert() {
      alert('Button clicked!')
    }
  },
  configureWebpack: {
    devtool: 'source-map'
  }
}
</script>

<style>
/* your custom styles here */
</style>
