<template>
  <v-app>
    <!-- Header -->
    <v-app-bar color="primary" dark app>
      <v-btn icon variant="plain" :ripple="false" href="http://localhost:5173/">
        <img
          src="/res/images/logo.svg"
          style="width: 40px; height: 40px"
        >
      </v-btn>
      
      <v-toolbar-title>Sapphire File Server</v-toolbar-title>
      
      <div style="display: flex; align-items: center; gap: 5px;">
        <span>Signed in as:</span>
        <v-btn prepend-icon="mdi-account-circle" stacked circle>
          admin
        </v-btn>
      </div>

      <v-progress-linear :active="isLoading" indeterminate rounded="pill" location="bottom" absolute></v-progress-linear>
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
      <v-container style="height: 100%;" @click.self="selectedFiles = []">
        <div v-shortkey="['ctrl', 'a']" @shortkey="selectAll()" style="display: none"></div>
        <div v-shortkey="['ctrl', 'i']" @shortkey="invertSelection()" style="display: none"></div>
        <div v-shortkey="['esc']" @shortkey="cancelOperation()" style="display: none"></div>
        <v-list v-if="currentPage === Pages.MyFiles" style="user-select: none;">
          <div class="d-flex justify-center ps-4">
          </div>
          <v-breadcrumbs>
            <v-btn width="30" height="30" icon="mdi-home" size="small" variant="text" @click="setCurrentPath('')">
            </v-btn>
            <v-breadcrumbs-divider v-if="currentPath !== ''"></v-breadcrumbs-divider>
            <div v-for="pathPart in getPathParts()">
              <v-btn height="30" class="text-none" variant="text" rounded="pill" style="padding: 0 8px;" @click="setCurrentPath(pathPart)">
                {{ getPathLastFolder(pathPart) }}
              </v-btn>
              <v-breadcrumbs-divider></v-breadcrumbs-divider>
            </div>
          </v-breadcrumbs>
          <v-divider></v-divider>
          <div class="d-flex justify-space-between">
            <div class="d-flex justify-start ga-2 pa-3">
              <v-btn class="text-none" prepend-icon="mdi-arrow-left-top" variant="text" rounded="pill" :disabled="currentPath === ''" @click="goBackDirectory()">Go back</v-btn>
            </div>
            <div class="d-flex justify-start ga-2 pa-3">
              <v-btn class="text-none" prepend-icon="mdi-content-cut" variant="text" rounded="pill"
              v-shortkey="['ctrl', 'x']" @shortkey="selectedFiles.length !== 0 ? cutSelected() : 0"
              @click="cutSelected()" :disabled="selectedFiles.length === 0">
                Cut
              </v-btn>
              <v-btn class="text-none" prepend-icon="mdi-content-copy" variant="text" rounded="pill"
              v-shortkey="['ctrl', 'c']" @shortkey="selectedFiles.length !== 0 ? copySelected() : 0"
              @click="copySelected()" :disabled="selectedFiles.length === 0">
                Copy
              </v-btn>
              <v-btn class="text-none" prepend-icon="mdi-content-paste" variant="text" rounded="pill"
              v-shortkey="['ctrl', 'v']" @shortkey="clipboard.length !== 0 ? pasteSelected() : 0"
              @click="pasteSelected()" :disabled="clipboard.length === 0">
                Paste
              </v-btn>
              <v-btn class="text-none" prepend-icon="mdi-form-textbox" variant="text" rounded="pill"
              v-shortkey="['f2']" @shortkey="selectedFiles.length !== 0 ? promptNewName() : 0"
              @click="promptNewName()" :disabled="selectedFiles.length === 0">
                Rename
              </v-btn>
              <v-btn class="text-none" prepend-icon="mdi-delete" variant="text" rounded="pill"
              v-shortkey="['del']" @shortkey="selectedFiles.length !== 0 ? promptDelete() : 0"
              @click="promptDelete()" :disabled="selectedFiles.length === 0">
                Delete
              </v-btn>
            </div>
            <div class="d-flex justify-start ga-2 pa-3">
              <v-btn class="text-none" prepend-icon="mdi-download" variant="text" rounded="pill" :disabled="selectedFiles.length === 0" @click="downloadSelectedFiles()">Download</v-btn>
              <v-btn class="text-none" prepend-icon="mdi-upload" variant="text" rounded="pill" >Upload</v-btn>
            </div>
          </div>
          <v-divider></v-divider>
          <v-list-item>
            <div style="display: flex; justify-content: space-between; font-weight: normal;">
              <v-btn
                class="text-none"
                variant="text"
                rounded="pill" 
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
          <v-list-item
            v-for="(file, index) in sortedFiles"
            :key="index"
            :value="file"
            :active="includesFile(selectedFiles, file)"
            :disabled="filesBeingCut.includes(currentPath + file.name)"
            color="primary"
            :style="{
              borderRadius: getFileBorderRadius(file) + ' !important',
              transition: 'border-radius 0.2s ease-in-out'
            }"
            @click="delayedToggleFileSelected(file)"
            @dblclick="changePath(file)"
          >
            <div style="display: flex; width: 100%; align-items: center;">
              <div style="flex: 2; display: flex; align-items: center; gap: 8px;">
                <v-icon :icon="getFileIcon(file)"></v-icon>
                {{ file.name }}
              </div>

              <div style="flex: 1;">
                {{ getFileTypeDescription(file) }}
              </div>

              <div style="flex: 1;">
                {{ getFileSize(file) }}
              </div>

              <div style="flex: 1; justify-self: right;">
                {{ getFileLastModifiedDate(file) }}
              </div>
            </div>
          </v-list-item>
        </v-list>
      </v-container>
      <v-dialog v-model="isRenaming" max-width="500">
        <v-card class="pa-6" rounded="xl" title="Enter a new name">
          <v-text-field v-model="fileNewName" autofocus label="New Name" :placeholder="fileNewName" persistent-placeholder type="input"></v-text-field>
          <v-card-actions>
            <v-btn @click="cancelOperation()">Cancel</v-btn>
            <v-btn @click="renameSelected()" color="primary">Ok</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="isDeleting" max-width="550">
        <v-card class="pa-6" rounded="xl" :title="`Do you want to delete the following (${selectedFiles.length}) items?`">
          <v-list class="ps-6">
            <div class="text-none d-flex ps-5 pb-1 pt-2 ga-2" v-for="item in selectedFiles">
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
            <v-btn @click="deleteSelected()" color="primary">Ok</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, toRaw, onMounted, onBeforeUnmount } from 'vue';

import { getFileIcon, fileExtensionDescriptions } from "./fileIcons.js";

const keysDown = ref(new Set());

function keyDownCallback(event) {
  keysDown.value.add(event.key);
}

function keyUpCallback(event) {
  keysDown.value.delete(event.key);
}

onMounted(() => {
  window.addEventListener('keydown', keyDownCallback);
  window.addEventListener('keyup', keyUpCallback);
  updateFilesAndDirectories();
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
const sortedFiles = ref([]);
const clipboard = ref([]);
const filesBeingCut = ref([]);

const isRenaming = ref(false);
const fileNewName = ref("");
const isDeleting = ref(false);

const isLoading = ref(false);

async function updateFilesAndDirectories() {
  try {
    const response = await fetch("http://127.0.0.1:8000/files/" + currentPath.value);
    if (!response.ok) {
      goBackDirectory();
      return;
    }
    const data = await response.json();
    
    filesAndDirectories.value = data;
    sortedFiles.value = sortFiles();
    selectedFiles.value = [];
  } catch (err) {
    console.error('Failed to load files:', err);
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
  isLoading.value = true;
  selectedFiles.value.forEach( (file, i, array) => {
      fetch("http://127.0.0.1:8000/download/" + currentPath.value + file.name)
      .then(res => res.blob())
      .then(blob => {
        const link = document.createElement('a');
        console.log("Creating blob...")
        const url = URL.createObjectURL(blob);
        console.log("Blob created")
        link.href = url;
        link.download = file.name;
        isLoading.value = false;
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

  sortedFiles.value = sortFiles();
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
  return array.findIndex((f) => areFilesSame(f, file));
}

function includesFile(array, file) {
  return getFileIndex(array, file) !== -1;
}

function sortFiles() {
  let sortingOrderMultipier = sortingOrder.value === SortingOrders.Ascending ? 1 : -1;

  switch (sortingMode.value) {
    case SortingModes.Name: return [...(filesAndDirectories.value)].sort(
      (a, b) => sortingOrderMultipier * a.name.localeCompare(b.name)
    ).reduce((result, element) => {
      result[(element.size < 0) ? 0 : 1].push(element);
      return result;
    },
    [[], []]).flat();
    case SortingModes.Type: return [...(filesAndDirectories.value)].sort(
      (a, b) => {
        let fileExtensionA = getFileNameExtension(a.name);
        let fileExtensionB = getFileNameExtension(b.name);
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

let selectedFiles = ref([]);

function toggleFileSelected(file) {
  const selectedFileIndex = getFileIndex(selectedFiles.value, file);
  if (keysDown.value.has("Control")) {
    if (selectedFileIndex === -1) {
      selectedFiles.value.push(file);
    }
    else {
      selectedFiles.value.splice(selectedFileIndex, 1);
    }
  }
  else if (keysDown.value.has("Shift") && selectedFiles.value.length !== 0) {
    let startIndex = getFileIndex(sortedFiles.value, selectedFiles.value[0]);
    let endIndex = getFileIndex(sortedFiles.value, file);
    
    if (endIndex < startIndex) {
      selectedFiles.value = toRaw(sortedFiles.value).slice(endIndex, startIndex + 1).reverse();
    }
    else {
      selectedFiles.value = toRaw(sortedFiles.value).slice(startIndex, endIndex + 1);
    }

  }
  else {
    if (selectedFileIndex === -1) {
      selectedFiles.value = [file];
    }
    else {
      selectedFiles.value = selectedFiles.value.length > 1 ? [file] : [];
    }
  }
}

function delayedToggleFileSelected(file) {
  setTimeout(toggleFileSelected, 150, file);
}

function deletePaths(paths) {
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
    updateFilesAndDirectories();
  });
}

function selectAll() {
  selectedFiles.value = [...sortedFiles.value];
}

function invertSelection() {
  let newSelection = [];
  sortedFiles.value.forEach((file) => {
    if (!includesFile(selectedFiles.value, file)) {
      newSelection.push(file);
    }
  });
  selectedFiles.value = newSelection;
}

function cutSelected() {
  clipboard.value = selectedFiles.value.map((file) => currentPath.value + file.name);
  filesBeingCut.value = [...clipboard.value];
}

function copySelected() {
  clipboard.value = selectedFiles.value.map((file) => currentPath.value + file.name);
}

function pasteSelected() {
  let filesBeforePaste = [...sortedFiles.value];
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
    });
    if (filesBeingCut.value.length !== 0) {
      deletePaths(filesBeingCut.value);
      filesBeingCut.value = [];
      clipboard.value = [];
    }
  });
  setTimeout(() => {
    updateFilesAndDirectories().then(() => {
      selectedFiles.value = [];
      sortedFiles.value.forEach((file) => {
        if (!includesFile(filesBeforePaste, file)) {
          selectedFiles.value.push(file);
        }
      });
    });
  }, 100);
}

function promptNewName() {
  isRenaming.value = true;
  fileNewName.value = selectedFiles.value[0].name;
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
      path: currentPath.value + selectedFiles.value[0].name,
      newName: fileNewName.value
    })
  }).then(_ => {
    fileNewName.value = "";
    updateFilesAndDirectories();
  });
}

function promptDelete() {
  isDeleting.value = true;
}

function deleteSelected() {
  deletePaths(selectedFiles.value.map((file) => currentPath.value + file.name));
  isDeleting.value = false;
}

function cancelOperation() {
  if (filesBeingCut.value.length !== 0) {
    filesBeingCut.value = [];
    clipboard.value = [];
  }
  if (isRenaming.value) {
    isRenaming.value = false;
    fileNewName.value = "";
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

function areFilesSame(a, b) {
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

function getFileLastModifiedDate(file) {
  const date = new Date(file.lastModified * 1000);

  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}\u202F/\u202F${month}\u202F/\u202F${day} \u202F${hour}:${minute}`;

}

function getFileNameExtension(fileName) {
  let i = fileName.lastIndexOf('.');
  if (i === -1) {
    return "";
  }
  return fileName.slice(i + 1);
}

function getFileTypeDescription(file) {
  if (file.size === -1) {
    return "File Folder";
  }

  let fileExtension = getFileNameExtension(file.name);
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
    updateFilesAndDirectories();
  }
  else {
    openFile(file);
  }
}

function getFileBorderRadius(file) {
  if (selectedFiles.value.findIndex(f => areFilesSame(f, file)) === -1) {
    return "25px 25px 25px 25px";
  }

  let i = sortedFiles.value.findIndex(f => areFilesSame(f, file));
  let doRoundTop = (i !== 0) ? selectedFiles.value.findIndex(f => areFilesSame(f, sortedFiles.value[i - 1])) === -1 : true;
  let doRoundBottom = (i !== sortedFiles.value.length - 1) ? selectedFiles.value.findIndex(f => areFilesSame(f, sortedFiles.value[i + 1])) === -1 : true;

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
  updateFilesAndDirectories();
}

function goBackDirectory() {
  const pathParts = getPathParts();
  if (pathParts.length === 1) {
    setCurrentPath("");
  }
  else {
    setCurrentPath(pathParts[pathParts.length - 2]);
  }
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
