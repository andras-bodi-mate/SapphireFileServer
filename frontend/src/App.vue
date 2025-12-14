<template>
  <v-app>
    <v-app-bar
      :color="theme.global.name.value === 'light' ? 'primary' : 'grey-darken-3'"
      style="z-index: 1000"
      app
    >
      <v-btn
        icon
        variant="plain"
        :ripple="false"
        href="https://bodi.homelinuxserver.org"
      >
        <img src="/res/images/logo.svg" style="width: 40px; height: 40px" />
      </v-btn>

      <v-toolbar-title>Sapphire File Server</v-toolbar-title>

      <div class="d-flex justify-space-between align-center ga-2 pa-3">
        <v-btn
          :icon="
            theme.global.name.value === 'dark'
              ? 'mdi-moon-waxing-crescent'
              : 'mdi-white-balance-sunny'
          "
          @click="switchTheme()"
        ></v-btn>
        <span>Signed in as:</span>
        <v-btn
          class="text-none"
          size="large"
          rounded="pill"
          prepend-icon="mdi-account-circle"
        >
          {{ username }}
          <v-menu activator="parent">
            <v-list style="border-radius: 28px">
              <v-list-item class="ml-2 mr-2" rounded="pill" @click="signOut()">
                <v-list-item-title> Sign out </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-btn>
      </div>
      <v-progress-linear
        :active="isZipping || isLoading"
        indeterminate
        rounded="pill"
        location="bottom"
        absolute
      ></v-progress-linear>
    </v-app-bar>

    <v-navigation-drawer app v-model="drawer" :rail="rail" permanent>
      <v-list :lines="false" density="compact" nav>
        <v-btn
          class="mb-2"
          size="small"
          :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
          variant="text"
          @click.stop="rail = !rail"
        ></v-btn>
        <v-tooltip
          v-for="(item, i) in navigationDrawerMenus"
          :key="i"
          :disabled="!rail"
          :text="item.text"
          location="right"
          transition="fade-transition"
          open-delay="750"
        >
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              :value="item"
              :active="item.page === currentPage"
              @click="handleNavigationDrawerClick(item)"
              color="primary"
            >
              <template #prepend>
                <v-icon :icon="item.icon"></v-icon>
              </template>

              <!-- Title visible only when drawer expanded -->
              <v-list-item-title
                v-if="!rail"
                v-text="item.text"
              ></v-list-item-title>
            </v-list-item>
          </template>
        </v-tooltip>
      </v-list>
    </v-navigation-drawer>

    <v-main @click="clearSelection()">
      <v-container
        @click.stop
        class="pl-10 pr-10"
        style="height: 100%; max-width: none"
      >
        <div
          v-shortkey="['ctrl', 'a']"
          @shortkey="isDialogOpen() ? 0 : selectAll()"
          style="display: none"
        ></div>
        <div
          v-shortkey="['ctrl', 'i']"
          @shortkey="isDialogOpen() ? 0 : invertSelection()"
          style="display: none"
        ></div>
        <div
          v-shortkey="['esc']"
          @shortkey="cancelOperation()"
          style="display: none"
        ></div>
        <div
          v-shortkey="['arrowdown']"
          @shortkey="isDialogOpen() ? 0 : moveSelection(1)"
          style="display: none"
        ></div>
        <div
          v-shortkey="['shift', 'arrowdown']"
          @shortkey="isDialogOpen() ? 0 : moveSelection(1)"
          style="display: none"
        ></div>
        <div
          v-shortkey="['arrowup']"
          @shortkey="isDialogOpen() ? 0 : moveSelection(-1)"
          style="display: none"
        ></div>
        <div
          v-shortkey="['shift', 'arrowup']"
          @shortkey="isDialogOpen() ? 0 : moveSelection(-1)"
          style="display: none"
        ></div>
        <v-list
          v-if="currentPage === Pages.MyFiles"
          class="pa-4 elevation-5"
          style="user-select: none"
          rounded="xl"
        >
          <!--Current path and search-->
          <div class="d-flex justify-space-between mb-2">
            <v-text-field
              ref="pathField"
              v-model="editablePath"
              size="small"
              label=""
              density="compact"
              rounded="pill"
              hide-details
              single-line
              class="no-underline no-text-field-data-padding rounded-pill w-100 pt-0 pb-0 pl-2 mr-8"
              :input-class="!isEditingPath ? 'text-transparent caret-transparent' : ''"
              :class="{'input-ml-6': isEditingPath}"
              @focus="focusedPathEditField()"
              @blur="setEditedPath()"
            >
              <v-breadcrumbs
                v-if="!isEditingPath"
                id="path"
                class="pa-0"
                @mousedown.stop
                @click.stop
              >
                <v-btn
                  width="30"
                  height="30"
                  icon="mdi-home"
                  size="small"
                  variant="text"
                  tabindex="-1"
                  @click.stop.prevent="setCurrentPath('')"
                >
                </v-btn>
                <v-breadcrumbs-divider
                  v-if="currentPath !== ''"
                ></v-breadcrumbs-divider>
                <div class="d-inline-flex" v-for="pathPart in getPathSubPaths()">
                  <v-btn
                    height="30"
                    class="text-none"
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    style="padding: 0 8px"
                    @click.stop.prevent="setCurrentPath(pathPart)"
                  >
                    {{ getPathLastFolder(pathPart) }}
                  </v-btn>
                  <v-breadcrumbs-divider
                    style="padding-top: 2px"
                  ></v-breadcrumbs-divider>
                </div>
              </v-breadcrumbs>
            </v-text-field>
            <div style="max-width: 400px; min-width: 200px">
              <v-text-field
                v-model="searchQuery"
                size="small"
                label="Search"
                density="compact"
                rounded="pill"
                append-inner-icon="mdi-magnify"
                hide-details
                single-line
                class="no-underline"
                style="max-width: 400px"
                v-shortkey="['enter']"
                @shortkey="search(searchQuery)"
                @input="search(searchQuery)"
                @click:append-inner="search(searchQuery)"
              ></v-text-field>
            </div>
          </div>
          <v-divider></v-divider>
          <div class="d-flex justify-space-between flex-wrap">
            <div class="d-flex justify-start pa-3">
              <v-btn
                class="text-none"
                prepend-icon="mdi-arrow-left-top"
                variant="text"
                rounded="pill"
                tabindex="-1"
                v-shortkey="['backspace']"
                @shortkey="
                  isDialogOpen() || currentPath === '' ? 0 : goBackDirectory()
                "
                :disabled="currentPath === ''"
                @click="goBackDirectory()"
              >
                Go back
              </v-btn>
              <v-tooltip
                text="Refresh"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    height="36"
                    width="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    v-shortkey="['ctrl', 'r']"
                    @shortkey="isDialogOpen() ? 0 : updateItems()"
                    @click="updateItems()"
                  >
                    <v-icon size="20">mdi-refresh</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
            </div>
            <div class="d-flex justify-start pa-3">
              <v-btn
                class="text-none"
                prepend-icon="mdi-folder-plus"
                variant="text"
                rounded="pill"
                tabindex="-1"
                @click="createNewFolder()"
                v-shortkey="['ctrl', 'shift', 'n']"
                @shortkey="isDialogOpen() ? 0 : createNewFolder()"
              >
                New Folder
              </v-btn>
              <v-btn
                class="text-none"
                prepend-icon="mdi-file-plus"
                variant="text"
                rounded="pill"
                tabindex="-1"
                @click="createNewFile()"
                v-shortkey="['alt', 'n']"
                @shortkey="isDialogOpen() ? 0 : createNewFile()"
              >
                New File
              </v-btn>
            </div>
            <div class="d-flex justify-start ga-3 pa-3">
              <v-tooltip
                text="Cut"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    height="36"
                    width="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    v-shortkey="['ctrl', 'x']"
                    @shortkey="
                      !isDialogOpen() && selectedItems.length !== 0
                        ? cutSelected()
                        : 0
                    "
                    @click="cutSelected()"
                    :disabled="selectedItems.length === 0"
                  >
                    <v-icon size="20">mdi-content-cut</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip
                text="Copy"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    width="36"
                    height="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    v-shortkey="['ctrl', 'c']"
                    @shortkey="
                      !isDialogOpen() && selectedItems.length !== 0
                        ? copySelected()
                        : 0
                    "
                    @click="copySelected()"
                    :disabled="selectedItems.length === 0"
                  >
                    <v-icon size="20">mdi-content-copy</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip
                text="Paste"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    width="36"
                    height="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    v-shortkey="['ctrl', 'v']"
                    @shortkey="
                      !isDialogOpen() && clipboard.length !== 0
                        ? pasteSelected()
                        : 0
                    "
                    @click="pasteSelected()"
                    :disabled="clipboard.length === 0"
                  >
                    <v-icon size="20">mdi-content-paste</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip
                text="Rename"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    width="36"
                    height="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    v-shortkey="['f2']"
                    @shortkey="
                      !isDialogOpen() && selectedItems.length === 1
                        ? promptNewName()
                        : 0
                    "
                    @click="promptNewName()"
                    :disabled="selectedItems.length !== 1"
                  >
                    <v-icon size="20">mdi-form-textbox</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip
                text="Delete"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    width="36"
                    height="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    v-shortkey="['del']"
                    @shortkey="
                      !isDialogOpen() && selectedItems.length !== 0
                        ? promptDelete()
                        : 0
                    "
                    @click="promptDelete()"
                    :disabled="selectedItems.length === 0"
                  >
                    <v-icon size="20">mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip
                text="Share"
                location="bottom"
                transition="fade-transition"
                open-delay="750"
              >
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    width="36"
                    height="36"
                    icon=""
                    variant="text"
                    rounded="pill"
                    tabindex="-1"
                    @click="promptShare()"
                    :disabled="selectedItems.length !== 1"
                  >
                    <v-icon size="20">mdi-share-variant</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
            </div>
            <div class="d-flex justify-start pa-3">
              <v-btn
                class="text-none"
                prepend-icon="mdi-information"
                variant="text"
                rounded="pill"
                tabindex="-1"
                @click="openDetails()"
                :disabled="selectedItems.length !== 1"
              >
                Details
              </v-btn>
            </div>
            <div class="d-flex justify-start pa-3">
              <v-btn
                class="text-none"
                prepend-icon="mdi-download"
                variant="text"
                rounded="pill"
                tabindex="-1"
                :disabled="selectedItems.length === 0"
                @click="downloadSelectedFiles()"
              >
                Download
              </v-btn>
              <v-btn
                class="text-none"
                prepend-icon="mdi-upload"
                variant="text"
                rounded="pill"
                tabindex="-1"
              >
                Upload
                <v-menu activator="parent">
                  <v-list style="border-radius: 28px">
                    <v-list-item
                      class="ml-2 mr-2"
                      rounded="pill"
                      @click="uploadFiles()"
                    >
                      <v-list-item-title> Upload files </v-list-item-title>
                    </v-list-item>
                    <v-list-item
                      class="ml-2 mr-2"
                      rounded="pill"
                      @click="uploadDirectory()"
                    >
                      <v-list-item-title> Upload directory </v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </v-btn>
            </div>
          </div>
          <v-divider></v-divider>
          <div class="d-flex w-100 mt-2">
            <div style="flex: 4">
              <!--Sorting controls-->
              <v-list-item>
                <div class="d-flex justify-start">
                  <span style="flex: 2">
                    <v-btn
                      class="text-none"
                      variant="text"
                      rounded="pill"
                      tabindex="-1"
                      @click="delayedChangeSorting(SortingModes.Name)"
                    >
                      File Name
                      <v-icon>
                        {{ getSortingIcon(SortingModes.Name) }}
                      </v-icon>
                    </v-btn>
                  </span>
                  <span style="flex: 1">
                    <v-btn
                      class="text-none"
                      variant="text"
                      rounded="pill"
                      tabindex="-1"
                      @click="delayedChangeSorting(SortingModes.Type)"
                    >
                      Type
                      <v-icon>
                        {{ getSortingIcon(SortingModes.Type) }}
                      </v-icon>
                    </v-btn>
                  </span>
                  <span style="flex: 1">
                    <v-btn
                      class="text-none"
                      variant="text"
                      rounded="pill"
                      tabindex="-1"
                      style="flex: 1"
                      @click="delayedChangeSorting(SortingModes.Size)"
                    >
                      Size
                      <v-icon>
                        {{ getSortingIcon(SortingModes.Size) }}
                      </v-icon>
                    </v-btn>
                  </span>
                  <span style="flex: 1">
                    <v-btn
                      class="text-none"
                      variant="text"
                      rounded="pill"
                      tabindex="-1"
                      style="flex: 1"
                      @click="delayedChangeSorting(SortingModes.LastModified)"
                    >
                      Last Modified
                      <v-icon>
                        {{ getSortingIcon(SortingModes.LastModified) }}
                      </v-icon>
                    </v-btn>
                  </span>
                </div>
              </v-list-item>
              <!--No connection banner-->
              <v-banner
                v-if="networkError"
                class="justify-center text-deep-orange"
              >
                <v-icon class="mr-3" size="large"> mdi-alert </v-icon>
                <v-banner-text>
                  Couldn't reach server. This could be because the server is
                  offline or due to bad internet connection.
                </v-banner-text>
              </v-banner>
              <!--No items to display banner-->
              <v-banner
                v-if="sortedItems.length == 0"
                class="justify-center text-grey"
              >
                <v-icon class="mr-3" size="large"> mdi-information </v-icon>
                <v-banner-text> No items to display. </v-banner-text>
              </v-banner>
              <!--Files-->
              <v-list-item
                v-if="sortedItems.length !== 0 && !networkError"
                v-for="(file, index) in sortedItems"
                :key="index"
                :value="file"
                :active="includesFile(selectedItems, file)"
                :disabled="itemsBeingCut.includes(currentPath + file.name)"
                :ref="
                  (el) => {
                    itemsComponent[file.name] = el;
                  }
                "
                tabindex="-1"
                color="primary"
                :style="{
                  borderRadius: getItemBorderRadius(file) + ' !important',
                  transition: 'border-radius 0.2s ease-in-out',
                }"
                @click="isLoading ? 0 : delayedToggleFileSelected(file)"
                @dblclick="isLoading ? 0 : changePath(file)"
                @contextmenu.prevent="openContextMenu($event, file)"
                v-shortkey="['enter']"
                @shortkey="
                  isLoading || selectedItems.length !== 1 || isDialogOpen()
                    ? 0
                    : changePath(selectedItems[0])
                "
              >
                <div style="display: flex; width: 100%; align-items: center">
                  <div
                    class="pr-2 ga-2 justify-start"
                    style="
                      flex: 2;
                      align-items: center;
                      white-space: nowrap;
                      overflow-y: hidden;
                      overflow-x: auto;
                      scrollbar-width: none;
                      text-overflow: ellipsis;
                    "
                  >
                    <v-icon :icon="getFileIcon(file)"></v-icon>
                    {{ file.name }}
                  </div>

                  <div
                    class="pl-2 pr-2"
                    style="
                      flex: 1;
                      align-items: center;
                      white-space: nowrap;
                      overflow-y: hidden;
                      overflow-x: auto;
                      scrollbar-width: none;
                      text-overflow: ellipsis;
                    "
                  >
                    {{ getItemTypeDescription(file) }}
                  </div>

                  <div
                    class="pl-2 pr-2"
                    style="
                      flex: 1;
                      align-items: center;
                      white-space: nowrap;
                      overflow-y: hidden;
                      overflow-x: auto;
                      scrollbar-width: none;
                      text-overflow: ellipsis;
                    "
                  >
                    {{ getFileSizeDescription(file.size) }}
                  </div>

                  <div
                    class="pl-2"
                    style="
                      flex: 1;
                      align-items: center;
                      white-space: nowrap;
                      overflow-y: hidden;
                      overflow-x: auto;
                      scrollbar-width: none;
                      text-overflow: ellipsis;
                    "
                  >
                    {{ getItemLastModifiedDate(file) }}
                  </div>
                </div>
                <v-menu
                  v-if="rightClickedItem === file"
                  v-model="isRightClickMenuOpen"
                  absolute
                  :close-on-content-click="true"
                  :open-on-click="false"
                  :style="{
                    position: 'absolute',
                    left: `${menuLocation.x}px`,
                    top: `${menuLocation.y}px`,
                  }"
                >
                  <v-list density="compact" class="pa-3" rounded="xl">
                    <v-list-item
                      rounded="pill"
                      prepend-icon="mdi-open-in-new"
                      size="small"
                      @click="changePath(file)"
                      :disabled="selectedItems.length !== 1"
                    >
                      <v-list-item-title>Open</v-list-item-title>
                    </v-list-item>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-share-variant"
                      @click="promptShare()"
                      :disabled="selectedItems.length !== 1"
                    >
                      <v-list-item-title>Share</v-list-item-title>
                    </v-list-item>
                    <v-divider class="mt-2 mb-2"></v-divider>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-content-cut"
                      @click="cutSelected()"
                      :disabled="selectedItems.length === 0"
                    >
                      <v-list-item-title>Cut</v-list-item-title>
                    </v-list-item>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-content-copy"
                      @click="copySelected()"
                      :disabled="selectedItems.length === 0"
                    >
                      <v-list-item-title>Copy</v-list-item-title>
                    </v-list-item>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-content-paste"
                      @click="pasteSelected()"
                      :disabled="clipboard.length === 0"
                    >
                      <v-list-item-title>Paste</v-list-item-title>
                    </v-list-item>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-form-textbox"
                      @click="promptNewName()"
                      :disabled="selectedItems.length !== 1"
                    >
                      <v-list-item-title>Rename</v-list-item-title>
                    </v-list-item>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-delete"
                      @click="promptDelete()"
                      :disabled="selectedItems.length === 0"
                    >
                      <v-list-item-title>Delete</v-list-item-title>
                    </v-list-item>
                    <v-divider class="mt-2 mb-2"></v-divider>
                    <v-list-item
                      size="small"
                      rounded="pill"
                      prepend-icon="mdi-information"
                      @click="openDetails()"
                      :disabled="selectedItems.length !== 1"
                    >
                      <v-list-item-title>Details</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </v-list-item>
            </div>
            <!--Preview-->
            <transition name="fade" mode="out-in">
              <div
                v-if="
                  (isLoadingPreview ||
                  imagePreviewUrl !== null ||
                  textPreview !== null ||
                  codePreview !== null) && 
                  (selectedItems.length === 1 && selectedItems[0].size > 0)
                "
                class="preview-box ml-5 mt-3 rounded-xl"
              >
                <div
                  v-if="isLoadingPreview"
                  class="d-flex align-center justify-center fill-height"
                  style="aspect-ratio: 4/3"
                >
                  <v-progress-circular
                    color="grey-lighten-4"
                    indeterminate
                  ></v-progress-circular>
                </div>
                <v-img
                  v-else-if="imagePreviewUrl !== null"
                  class="rounded-lg"
                  :src="imagePreviewUrl"
                ></v-img>
                <p
                  v-else-if="textPreview !== null"
                  class="ma-5"
                  style="
                    user-select: text;
                    -webkit-user-select: text;
                    overflow: auto;
                    white-space: pre-line;
                  "
                >
                  {{ textPreview }}
                </p>
                <highlightjs
                  v-else-if="codePreview !== null"
                  style="
                    user-select: text;
                    -webkit-user-select: text;
                    overflow: auto;
                  "
                  :language="codePreviewLanguage"
                  :code="codePreview"
                  :key="codePreviewHighlightKey"
                />
              </div>
            </transition>
          </div>
        </v-list>
        <div
          class="d-flex flex-column align-end justify-end ma-5"
          style="position: fixed; bottom: 0px; right: 0px"
        >
          <div class="pa-0">
            <p>
              {{
                `${selectedItems.length} / ${sortedItems.length} items selected`
              }}
            </p>
          </div>
          <v-list
            class="pa-3 elevation-5"
            rounded="xl"
            style="max-height: 500px"
            v-if="itemsBeingUploadedInfo.length !== 0"
          >
            <div class="d-flex ma-3 justify-space-between align-center ga-10">
              <p size="x-large">
                {{ `Uploading ${itemsBeingUploadedInfo.length} items` }}
              </p>
              <v-btn
                icon="mdi-close"
                variant="text"
                @click="cancelAllUploads()"
              ></v-btn>
            </div>
            <v-divider></v-divider>
            <div class="d-flex ma-3 align-center">
              <p>
                {{
                  uploadRemainingSeconds > 0
                    ? `${
                        uploadRemainingSeconds >= 3600
                          ? `${Math.floor(
                              uploadRemainingSeconds / 3600,
                            )} hours `
                          : ""
                      }${
                        uploadRemainingSeconds >= 60
                          ? `${Math.floor(uploadRemainingSeconds / 60) % 60}
                minutes and `
                          : ""
                      }${uploadRemainingSeconds < 3600 ? `${uploadRemainingSeconds % 60} seconds` : ""} left...`
                    : "Calculating remaining time..."
                }}
              </p>
            </div>
            <v-divider></v-divider>
            <div
              v-for="itemInfo in itemsBeingUploadedInfo"
              class="d-flex ma-3 align-center justify-space-between"
            >
              <div class="d-flex ga-3">
                <v-icon>{{ getFileIcon(itemInfo) }}</v-icon>
                <p>{{ itemInfo.name }}</p>
              </div>
              <v-hover>
                <template v-slot:default="{ isHovering, props }">
                  <v-span v-bind="props">
                    <v-tooltip
                      v-bind="props"
                      text="Cancel"
                      location="top"
                      transition="fade-transition"
                      open-delay="750"
                    >
                      <template v-slot:activator="{ props }">
                        <v-btn
                          icon="mdi-close"
                          v-bind="props"
                          size="30"
                          :loading="isHovering ? false : true"
                          variant="text"
                          @click="cancelUpload(itemInfo)"
                        >
                          <template #loader>
                            <v-progress-circular
                              size="25"
                              :indeterminate="itemInfo.progress === -1"
                              :model-value="itemInfo.progress"
                            ></v-progress-circular>
                          </template>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </v-span>
                </template>
              </v-hover>
            </div>
          </v-list>
        </div>
      </v-container>
      <v-dialog v-model="isRenaming" max-width="500">
        <v-card class="ps-2 pt-6 pb-6" rounded="xl" title="Enter a new name">
          <v-text-field
            class="ml-10 mr-10"
            variant="outlined"
            v-model="itemNewName"
            autofocus
            label="New Name"
            :placeholder="itemNewName"
            persistent-placeholder
            type="input"
            v-shortkey="['enter']"
            @shortkey="isRenaming ? renameSelected() : 0"
          ></v-text-field>
          <v-card-actions>
            <v-btn @click="cancelOperation()">Cancel</v-btn>
            <v-btn autofocus @click="renameSelected()" color="primary"
              >Ok</v-btn
            >
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="isDeleting" max-width="550">
        <v-card
          class="pa-6"
          rounded="xl"
          :title="`Do you want to delete the following (${selectedItems.length}) items?`"
          v-shortkey="['enter']"
          @shortkey="isDeleting ? deleteSelected() : 0"
        >
          <v-list class="ps-6">
            <div
              class="text-none d-flex ps-5 pb-1 pt-2 ga-2"
              v-for="item in selectedItems"
            >
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
            <v-btn autofocus @click="deleteSelected()" color="primary"
              >Ok</v-btn
            >
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="isSharing" max-width="550">
        <v-card
          class="pa-6"
          rounded="xl"
          :title="`Sharing item`"
          v-shortkey="['enter']"
          @shortkey="isSharing ? shareSelected() : 0"
        >
          <v-row class="justify-center ml-5 mr-5" :cols="2">
            <v-col>
              <v-radio-group v-model="expirationTime" label="Link expires in:">
                <v-radio
                  class="ms-5"
                  label="1 Hour"
                  :value="3600"
                  @click="generatedLink = ''"
                ></v-radio>
                <v-radio
                  class="ms-5"
                  label="5 Hours"
                  :value="18000"
                  @click="generatedLink = ''"
                ></v-radio>
                <v-radio
                  class="ms-5"
                  label="1 Day"
                  :value="86400"
                  @click="generatedLink = ''"
                ></v-radio>
                <v-radio
                  class="ms-5"
                  label="1 Week"
                  :value="604800"
                  @click="generatedLink = ''"
                ></v-radio>
                <v-radio
                  class="ms-5"
                  label="Custom Time"
                  :value="-1"
                  @click="generatedLink = ''"
                ></v-radio>
              </v-radio-group>
            </v-col>
            <v-col class="mt-9" v-if="expirationTime === -1">
              <v-number-input
                density="comfortable"
                v-model="customExpirationTimeDays"
                label="Days"
                controlVariant="stacked"
                variant="outlined"
                inset
                :min="0"
                @update:model-value="generatedLink = ''"
              ></v-number-input>
              <v-number-input
                density="comfortable"
                v-model="customExpirationTimeHours"
                label="Hours"
                controlVariant="stacked"
                variant="outlined"
                inset
                :min="0"
                :max="23"
                @update:model-value="generatedLink = ''"
              ></v-number-input>
              <v-number-input
                density="comfortable"
                v-model="customExpirationTimeMinutes"
                label="Minutes"
                controlVariant="stacked"
                variant="outlined"
                inset
                :min="0"
                :max="59"
                @update:model-value="generatedLink = ''"
              ></v-number-input>
            </v-col>
          </v-row>
          <v-divider></v-divider>
          <div
            v-if="generatedLink === ''"
            class="d-flex justify-center mb-15 mt-5"
          >
            <v-btn
              width="150"
              class="text-none"
              variant="tonal"
              :loading="isGeneratingLink"
              @click="generateLink()"
              :disabled="!isExpirationTimeCorrect()"
              >Generate Link</v-btn
            >
          </div>
          <v-row v-else class="pa-5 pl-10 pr-10 justify-center">
            <v-col cols="auto" class="d-flex align-center justify-end">
              <v-btn
                class="text-none"
                variant="tonal"
                prepend-icon="mdi-link"
                rounded="pill"
                color="primary"
                @click="copyLink()"
              >
                Copy
              </v-btn>
            </v-col>

            <v-col class="d-flex">
              <v-text-field
                v-model="generatedLink"
                density="comfortable"
                hide-details
                readonly
                class="flex-grow-1"
              />
            </v-col>
          </v-row>

          <v-card-actions>
            <v-btn v-if="generatedLink.length === 0" @click="cancelOperation()"
              >Cancel</v-btn
            >
            <v-btn autofocus @click="cancelOperation()" color="primary"
              >Done</v-btn
            >
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="isViewingDetails" max-width="550">
        <v-card
          class="pa-6"
          rounded="xl"
          :title="`${selectedItems[0].name} details`"
        >
          <v-list class="d-flex flex-column ps-6 ga-2">
            <div class="text-none d-flex ga-2">
              <v-icon>
                {{ getFileIcon(selectedItems[0]) }}
              </v-icon>
              <p>
                {{ selectedItems[0].name }}
              </p>
            </div>
            <p>
              {{
                `Type of file: ${getItemTypeDescription(selectedItems[0])}${
                  selectedItems[0].size > 0
                    ? getItemNameExtension(selectedItems[0].name)
                    : ""
                }`
              }}
            </p>
            <v-divider></v-divider>
            <p>
              {{ `Location: ${currentPath !== "" ? currentPath : "/"}` }}
            </p>
            <p>
              {{ `Size: ${getItemSizeDescription(selectedItems[0])}` }}
            </p>
            <p v-if="selectedItems[0].size < 0">
              {{
                `Number of files: ${directoryDetails.numFiles >= 0 ? directoryDetails.numFiles : "Loading..."}`
              }}
            </p>
            <p v-if="selectedItems[0].size < 0">
              {{
                `Number of subdirectories: ${
                  directoryDetails.numSubdirectories >= 0
                    ? directoryDetails.numSubdirectories
                    : "Loading..."
                }`
              }}
            </p>
            <v-divider></v-divider>
            <p>
              {{
                `Created: ${new Date(itemDetails.created * 1000).toString()}`
              }}
            </p>
            <p>
              {{
                `Last modified: ${new Date(itemDetails.lastModified * 1000).toString()}`
              }}
            </p>
            <p>
              {{
                `Last accessed: ${new Date(itemDetails.lastAccessed * 1000).toString()}`
              }}
            </p>
            <v-divider></v-divider>
            <div v-if="itemGeneralInfo !== null">
              <div v-if="typeof itemGeneralInfo == 'object'">
                <div v-for="[key, value] of Object.entries(itemGeneralInfo)">
                  <span v-if="value !== null">{{ `${key}: ` }}</span>
                  <span v-if="value !== null">{{ value }}</span>
                </div>
              </div>
              <span v-else>{{ itemGeneralInfo }}</span>
              <v-treeview v-if="itemMetadata !== null" density="compact" fluid indent-lines="default" :items="itemMetadata" item-value="id"></v-treeview>
            </div>
            <div class="d-flex align-center ga-3" v-else-if="selectedItems[0].size >= 0">
              <p>Loading metadata</p>
              <v-progress-circular size="25" indeterminate></v-progress-circular>
            </div>
          </v-list>
          <v-card-actions>
            <v-btn autofocus @click="closeDetails()" color="primary">Ok</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-main>
    <v-snackbar
      v-model="linkCopied"
      timeout="2000"
      rounded="pill"
      color="success"
      class="d-flex justify-center"
    >
      Link successfully copied.
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, reactive, computed, toRaw, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useTheme } from "vuetify";
import VueCookies from "vue-cookies";
import { getFileIcon, fileExtensionDescriptions } from "./fileIcons.js";
import Fuse from "fuse.js";
import { Upload } from "tus-js-client";
import { lookup } from "mime-types";
import 'highlight.js/lib/common';

const theme = useTheme();
const keysDown = ref(new Set());
const username = ref("");

function keyDownCallback(event) {
  keysDown.value.add(event.key);
}

function keyUpCallback(event) {
  keysDown.value.delete(event.key);
}

onMounted(() => {
  checkStoredTheme();
  window.addEventListener("keydown", keyDownCallback);
  window.addEventListener("keyup", keyUpCallback);
  fetch("/api/state").then(async (response) => {
    response = await response.json();
    if (response.status == "OK" && response.data.authentication_level !== 0) {
      username.value = response.data.username;
    } else {
      window.location.reload();
    }
  });
  updateItems();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", keyDownCallback);
  window.removeEventListener("keyup", keyUpCallback);
});

const Pages = {
  MyFiles: 0,
  Recent: 1,
  Plex: 2,
  Backups: 3,
};

const SortingOrders = {
  Ascending: 1,
  Descending: 2,
};

const SortingModes = {
  Name: 0,
  Type: 1,
  Size: 2,
  LastModified: 3,
  Search: 4,
};

const darkTheme = "tokyo-night-dark";
const lightTheme = "stackoverflow-light";
const currentPage = ref(Pages.MyFiles);
const rail = ref(true);
const sortingOrder = ref(SortingOrders.Ascending);
const sortingMode = ref(SortingModes.Name);

const items = ref([]);
const sortedItems = ref([]);
const itemsComponent = ref({});
const clipboard = ref([]);
const itemsBeingCut = ref([]);
const selectedItems = ref([]);
const menuLocation = ref({ x: 0, y: 0 });
const rightClickedItem = ref(null);

const drawer = ref(true);
const currentPath = ref("");
const isRenaming = ref(false);
const itemNewName = ref("");
const isDeleting = ref(false);
const isSharing = ref(false);
const isViewingDetails = ref(false);
const isRightClickMenuOpen = ref(false);
const expirationTime = ref(86400);
const customExpirationTimeDays = ref(0);
const customExpirationTimeHours = ref(0);
const customExpirationTimeMinutes = ref(0);
const isGeneratingLink = ref(false);
const generatedLink = ref("");
const linkCopied = ref(false);
const itemsBeingUploadedInfo = ref([]);
const uploadedItems = ref([]);
const uploadRemainingSeconds = ref(0);
const isZipping = ref(false);
const isLoading = ref(false);
const networkError = ref(false);
const itemDetails = ref({});
const directoryDetails = ref({});
const imagePreviewUrl = ref(null);
const textPreview = ref(null);
const codePreview = ref(null);
const codePreviewLanguage = ref(null);
const codePreviewHighlightKey = ref(0);
const isLoadingPreview = ref(false);
const searchQuery = ref("");
const itemGeneralInfo = ref(null);
const itemMetadata = ref(null);
const isEditingPath = ref(false);
const editedPath = ref("");
const pathField = ref(null);

const editablePath = computed({
  get() {
    return isEditingPath.value ? editedPath.value : '';
  },
  set(val) {
    editedPath.value = val;
  }
});

function switchTheme() {
  theme.toggle();
  setSyntaxHighlightingTheme(theme.current.value.dark ? darkTheme : lightTheme);
  VueCookies.set("app.themeCookie", theme.current.value.dark);
}

function checkStoredTheme() {
  let themeCookie = VueCookies.get("app.themeCookie");
  if (theme.current.value.dark.toString() !== themeCookie) {
    switchTheme();
  }
}

async function updateItems() {
  try {
    isLoading.value = true;
    const response = await fetch("/files/" + currentPath.value);
    if (response.redirected) {
      window.location.pathname = "/";
    }
    if (!response.ok) {
      setCurrentPath("");
      isLoading.value = false;
      networkError.value = true;
      return;
    }
    const data = await response.json();

    networkError.value = false;
    items.value = data;
    sortedItems.value = sortFiles();
    clearSelection();
    resetPreview();
    isLoading.value = false;
  } catch (err) {
    setCurrentPath("");
    isLoading.value = false;
    networkError.value = true;
  }
}

async function openFile(file) {
  fetch("/download/" + currentPath.value + file.name)
    .then((res) => {
      if (res.redirected) {
        window.location.pathname = "/";
      }
      return res.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    })
    .catch((err) => console.error("Error fetching file:", err));
}

async function downloadSelectedFiles() {
  isZipping.value = true;
  selectedItems.value.forEach((file, i, array) => {
    fetch("/download/" + currentPath.value + file.name + "/")
      .then((res) => res.blob())
      .then((blob) => {
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.download = file.size >= 0 ? file.name : file.name + ".zip";
        isZipping.value = false;
        link.click();
        URL.revokeObjectURL(url);
      });
  });
}

function createUpload(
  file,
  itemInfo,
  onProgress = () => {},
  onSuccess = () => {},
) {
  console.log("Creating upload for", itemInfo.name);
  return new Upload(file, {
    endpoint: "/upload/",
    retryDelays: [0, 1000, 2000, 3000, 4000],
    uploadStalledRetryDelay: 0,
    chunkSize: 8 * 1024 * 1024,
    metadata: {
      filename: file.name,
      filetype: lookup(file.name),
      directory: itemInfo.directory,
    },
    onError: function (error) {
      console.error("Failed because: " + error + "\n" + new Error().stack);
    },
    onProgress: function (bytesUploaded, bytesTotal) {
      var percentage = (bytesUploaded / bytesTotal) * 100;
      console.log(bytesUploaded, bytesTotal, percentage.toFixed(2) + "%");
      itemInfo.bytesUploaded = bytesUploaded;
      itemInfo.progress = percentage;
      if (itemInfo.uploadStartTime === -1) {
        itemInfo.uploadStartTime = Date.now() / 1000;
        itemInfo.estimatedTimeRemaining = 60;
      } else {
        itemInfo.estimatedTimeRemaining = Math.round(
          (bytesTotal - bytesUploaded) /
            (bytesUploaded / (Date.now() / 1000 - itemInfo.uploadStartTime)),
        );
      }

      uploadRemainingSeconds.value = 0;
      for (const itemInfo of itemsBeingUploadedInfo.value) {
        uploadRemainingSeconds.value = Math.max(
          uploadRemainingSeconds.value,
          itemInfo.estimatedTimeRemaining,
        );
      }

      onProgress();
    },
    onSuccess: function () {
      uploadedItems.value.push(itemInfo);
      const index = itemsBeingUploadedInfo.value.indexOf(itemInfo);
      if (index !== -1) {
        itemsBeingUploadedInfo.value.splice(
          itemsBeingUploadedInfo.value.indexOf(itemInfo),
          1,
        );
      }
      onSuccess();
    },
  });
}

async function uploadFiles() {
  var input = document.createElement("input");
  input.type = "file";
  input.multiple = true;
  input.onchange = async (e) => {
    const uploads = [];
    let lastItemUpdate = 0;

    for (const file of input.files) {
      for (const itemInfo of itemsBeingUploadedInfo.value) {
        if (
          itemInfo.name === file.name &&
          itemInfo.directory === currentPath.value
        ) {
          continue;
        }
      }
      let itemInfo = reactive({
        name: file.name,
        size: file.size,
        bytesUploaded: 0,
        progress: -1,
        directory: currentPath.value,
        uploadStartTime: -1,
        estimatedTimeRemaining: -1,
        upload: null,
      });
      itemsBeingUploadedInfo.value.push(itemInfo);

      let newUpload = createUpload(
        file,
        itemInfo,
        () => {},
        () => {
          let now = Date.now();
          if (now - lastItemUpdate > 1000) {
            updateItems();
            lastItemUpdate = now;
          }
        },
      );
      uploads.push(newUpload);
      itemInfo.upload = newUpload;
    }

    for (const upload of uploads) {
      // Check if there are any previous uploads to continue.
      upload.findPreviousUploads().then(function (previousUploads) {
        // Found previous uploads so we select the first one.
        if (previousUploads.length) {
          upload.resumeFromPreviousUpload(previousUploads[0]);
        }

        // Start the upload
        upload.start();
      });
    }
  };
  input.click();
}

async function uploadDirectory() {
  var input = document.createElement("input");
  input.type = "file";
  input.directory = "true";
  input.webkitdirectory = "true";
  const uploadPath = currentPath.value;

  input.onchange = async (e) => {
    const uploads = [];
    let numFilesUploading = 0;
    let numFilesUploaded = 0;

    const firstFile = input.files[0];
    const directoryName = firstFile.webkitRelativePath.slice(
      0,
      firstFile.webkitRelativePath.indexOf("/"),
    );

    let directoryInfo = reactive({
      name: directoryName,
      size: -1,
      progress: -1,
      directory: uploadPath,
      uploadStartTime: -1,
      estimatedTimeRemaining: -1,
      children: [],
      upload: null,
    });
    itemsBeingUploadedInfo.value.push(directoryInfo);

    const processFile = async (file) => {
      let fileInfo = {
        name: file.name,
        size: file.size,
        directory: getPathParent(uploadPath + file.webkitRelativePath),
        bytesUploaded: 0,
        progress: -1,
        uploadStartTime: -1,
        estimatedTimeRemaining: -1,
        upload: null,
      };

      const newUpload = createUpload(
        file,
        fileInfo,
        () => {
          if (numFilesUploading < input.files.length) {
            numFilesUploading++;
            if (numFilesUploading === input.files.length) {
              directoryInfo.uploadStartTime = Date.now() / 1000;
            }
          }

          let totalBytes = 0;
          let totalUploaded = 0;
          for (const info of directoryInfo.children) {
            totalBytes += info.size;
            totalUploaded += info.bytesUploaded;
          }

          console.log("totalBytes, totalUploaded", totalBytes, totalUploaded);

          if (numFilesUploading === input.files.length) {
            directoryInfo.progress = (totalUploaded / totalBytes) * 100;
            directoryInfo.estimatedTimeRemaining = Math.round(
              (totalBytes - totalUploaded) /
                (totalUploaded /
                  (Date.now() / 1000 - directoryInfo.uploadStartTime)),
            );
          }
        },
        () => {
          numFilesUploaded++;
          if (numFilesUploaded === input.files.length) {
            updateItems();
            itemsBeingUploadedInfo.value.splice(
              itemsBeingUploadedInfo.value.indexOf(directoryInfo),
              1,
            );
          }
        },
      );
      fileInfo.upload = newUpload;

      directoryInfo.children.push(fileInfo);
      uploads.push(newUpload);
    };

    const filePromises = new Array(input.files.length);

    for (const file of input.files) {
      console.log("Uploading", file.name);
      const promise = processFile(file);
      filePromises.push(promise);
      //await delay(25); // Delay of 25 milliseconds
    }
    console.log("Waiting for the file promises...");
    Promise.all(filePromises).then((_) => {
      console.log("File promises completed");

      uploads.forEach(async (upload) => {
        console.log("Beginning upload...");
        // Check if there are any previous uploads to continue.
        upload.findPreviousUploads().then(function (previousUploads) {
          // Found previous uploads so we select the first one.
          if (previousUploads.length) {
            upload.resumeFromPreviousUpload(previousUploads[0]);
          }
          // Start the upload
          upload.start();
        });
        await delay(100);
      });
    });
  };
  input.click();
}

function cancelUpload(cancelledItemInfo) {
  itemsBeingUploadedInfo.value.splice(
    itemsBeingUploadedInfo.value.indexOf(cancelledItemInfo),
    1,
  );
  if (cancelledItemInfo.size === -1) {
    for (const itemInfo of cancelledItemInfo.children) {
      cancelUpload(itemInfo);
    }
  } else {
    if (cancelledItemInfo.upload !== null) {
      cancelledItemInfo.upload.abort(true);
    }
  }
}

function cancelAllUploads() {
  for (const itemInfo of itemsBeingUploadedInfo.value) {
    cancelUpload(itemInfo);
  }
  itemsBeingUploadedInfo.value = [];
}

async function getDirectorySize(path) {
  let textDecoder = new TextDecoder();
  fetch("/directorySize/" + path)
    .then(async (response) => {
      if (!response.ok) {
        response.text().then((text) => {
          throw new Error(text);
        });
      }
      return response.body;
    })
    .then(async (body) => {
      const reader = body.getReader();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        const str = textDecoder.decode(value);
        buffer += str;
        const lastNewLine = buffer.lastIndexOf("\n");
        if (lastNewLine === -1) {
          continue;
        }
        const penultimateNewLine = buffer.lastIndexOf("\n", lastNewLine - 1);
        const json = JSON.parse(
          buffer.substring(penultimateNewLine + 1, lastNewLine),
        );
        buffer = buffer.substring(lastNewLine + 1);

        directoryDetails.value = json;
      }
    });
}

function changeSorting(newMode) {
  if (sortingMode.value !== newMode) {
    sortingMode.value = newMode;
    sortingOrder.value = SortingOrders.Ascending;
  } else {
    sortingOrder.value =
      sortingOrder.value === SortingOrders.Ascending
        ? SortingOrders.Descending
        : SortingOrders.Ascending;
  }

  sortedItems.value = sortFiles();
}

function delayedChangeSorting(newMode) {
  setTimeout(changeSorting, 175, newMode);
}

function getSortingIcon(mode) {
  if (sortingMode.value !== mode) {
    return "";
  }
  switch (sortingOrder.value) {
    case SortingOrders.Ascending:
      return "mdi-arrow-down";
    case SortingOrders.Descending:
      return "mdi-arrow-up";
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
  const component = itemsComponent.value[file.name];
  if (!component) return 0;

  const element = component.$el;

  const rect = element.getBoundingClientRect();
  if (rect.bottom < 0) {
    return -1;
  } else if (rect.top > window.innerHeight) {
    return 1;
  }
  return 0;
}

function sortFiles() {
  if (sortingMode.value === SortingModes.Search) {
    sortingMode.value = SortingModes.Name;
  }
  let sortingOrderMultipier =
    sortingOrder.value === SortingOrders.Ascending ? 1 : -1;

  switch (sortingMode.value) {
    case SortingModes.Name:
      return [...items.value]
        .sort(
          (a, b) => sortingOrderMultipier * compareFileNames(a.name, b.name),
        )
        .reduce(
          (result, element) => {
            result[element.size < 0 ? 0 : 1].push(element);
            return result;
          },
          [[], []],
        )
        .flat();
    case SortingModes.Type:
      return [...items.value].sort((a, b) => {
        let fileExtensionA = getItemNameExtension(a.name);
        let fileExtensionB = getItemNameExtension(b.name);
        return (
          sortingOrderMultipier * fileExtensionA.localeCompare(fileExtensionB)
        );
      });
    case SortingModes.Size:
      return [...items.value].sort(
        (a, b) => sortingOrderMultipier * (a.size - b.size),
      );
    case SortingModes.LastModified:
      return [...items.value].sort(
        (a, b) => sortingOrderMultipier * (a.lastModified - b.lastModified),
      );
  }
}

function toggleFileSelected(file) {
  const selectedFileIndex = getFileIndex(selectedItems.value, file);
  if (keysDown.value.has("Control")) {
    if (selectedFileIndex === -1) {
      selectedItems.value.push(file);
    } else {
      selectedItems.value.splice(selectedFileIndex, 1);
    }
  } else if (keysDown.value.has("Shift") && selectedItems.value.length !== 0) {
    let startIndex = getFileIndex(sortedItems.value, selectedItems.value[0]);
    let endIndex = getFileIndex(sortedItems.value, file);

    if (endIndex < startIndex) {
      selectedItems.value = toRaw(sortedItems.value)
        .slice(endIndex, startIndex + 1)
        .reverse();
    } else {
      selectedItems.value = toRaw(sortedItems.value).slice(
        startIndex,
        endIndex + 1,
      );
    }
  } else {
    if (
      selectedFileIndex === -1 ||
      (selectedFileIndex !== -1 && selectedItems.value.length > 1)
    ) {
      selectedItems.value = [file];
    } else {
      selectedItems.value = [];
    }
  }
  if (selectedItems.value.length === 1) {
    resetPreview();
    if (selectedItems.value[0].size >= 0) {
      getPreview(selectedItems.value[0]);
    }
  } else {
    resetPreview();
  }
}

function delayedToggleFileSelected(file) {
  setTimeout(toggleFileSelected, 150, file);
}

function moveSelection(direction) {
  if (keysDown.value.has("Control")) {
    return;
  }
  let doMoveSelection = true;
  if (selectedItems.value.length == 0) {
    selectedItems.value = [sortedItems.value[0]];
    doMoveSelection = false;
  } else if (selectedItems.value.length != 1 && !keysDown.value.has("Shift")) {
    selectedItems.value = [selectedItems.value[selectedItems.value.length - 1]];
    doMoveSelection = false;
  }
  let selectionEndIndex = getFileIndex(
    sortedItems.value,
    selectedItems.value[selectedItems.value.length - 1],
  );

  if (
    (selectionEndIndex === 0 && direction === -1) ||
    (selectionEndIndex === sortedItems.value.length - 1 && direction === 1)
  ) {
    doMoveSelection = false;
  }

  let file = selectedItems.value[selectedItems.value.length - 1];
  if (doMoveSelection) {
    file = sortedItems.value[selectionEndIndex + direction];
    toggleFileSelected(file);
  }

  const fileScreenPosition = getFileScreenPosition(file);
  if (fileScreenPosition === 0) {
    return;
  }
  window.scrollBy({
    top: fileScreenPosition * window.innerHeight * 1.0, // nearly a full page
    behavior: "smooth",
  });
}

function deletePaths(paths) {
  fetch("/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      mode: "delete",
    },
    body: JSON.stringify({
      paths: paths,
    }),
  }).then((_) => {
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

function clearSelection() {
  selectedItems.value = [];
}

function cutSelected() {
  clipboard.value = selectedItems.value.map(
    (file) => currentPath.value + file.name,
  );
  itemsBeingCut.value = [...clipboard.value];
}

function copySelected() {
  clipboard.value = selectedItems.value.map(
    (file) => currentPath.value + file.name,
  );
}

function pasteSelected() {
  const numCopiedItems = selectedItems.value.length;
  let newSelectionNames = [];
  clearSelection();
  clipboard.value.forEach((path) => {
    fetch("/modify/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        mode: "copy",
      },
      body: JSON.stringify({
        source: path,
        destination: currentPath.value,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("There was an error while copying an item.");
        }
        return response.json();
      })
      .then((response) => {
        newSelectionNames.push(response.name);
        if (newSelectionNames.length === numCopiedItems) {
          updateItems().then((_) => {
            selectedItems.value = sortedItems.value.filter(
              (file) => file.name in newSelectionNames,
            );
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
  fetch("/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      mode: "rename",
    },
    body: JSON.stringify({
      path: currentPath.value + selectedItems.value[0].name,
      newName: itemNewName.value.trim(),
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("There was an error while renaming the item.");
      }
      return response.json();
    })
    .then((_) => {
      itemNewName.value = "";
      updateItems();
    });
  isRenaming.value = false;
}

function promptDelete() {
  isDeleting.value = true;
}

function deleteSelected() {
  deletePaths(selectedItems.value.map((file) => currentPath.value + file.name));
  isDeleting.value = false;
}

function generateTreeviewData(data, startId = 1, title = "Streams") {
  let id = startId;

  const node = { id: id++, title, children: [] };

  if (Array.isArray(data)) {
    // If array → build children for each element
    for (const [i, item] of data.entries()) {
      if (typeof item === "object" && item !== null) {
        const { data: childNode, nextId } = generateTreeviewData(item, id, title.slice(0, title.length - 1) + ' ' + (i + 1));
        id = nextId;
        node.children.push(childNode);
      } else {
        node.children.push({ id: id++, title: String(item) });
      }
    }
  } else if (typeof data === "object") {
    // If object → keys become children
    for (const key in data) {
      const value = data[key];

      if (typeof value === "object" && value !== null) {
        const { data: childNode, nextId } = generateTreeviewData(value, id, key);
        id = nextId;
        node.children.push(childNode);
      } else {
        node.children.push({ id: id++, title: `${key}: ${value}` });
      }
    }
  }

  return { data: node, nextId: id };
}

function openDetails() {
  itemGeneralInfo.value = null;
  itemMetadata.value = null;
  isViewingDetails.value = true;
  directoryDetails.value = {
    size: -1,
    numFiles: -1,
    numSubdirectories: -1,
  };
  fetch("/details/" + currentPath.value).then((response) => {
    response.json().then((body) => {
      itemDetails.value = body;
    });
  });
  if (selectedItems.value[0].size < 0) {
    getDirectorySize(currentPath.value + selectedItems.value[0].name);
  } else {
    fetch("/metadata/" + currentPath.value + selectedItems.value[0].name).then(
      (response) => {
        if (!response.ok) {
          response.text().then((text) => {
            itemGeneralInfo.value = { Error: text };
          });
        } else {
          response.json().then((body) => {
            if ("error" in body) {
              itemGeneralInfo.value = body.error;
            }
            else {
              itemGeneralInfo.value = body.general;
              console.log(generateTreeviewData(body.all).data);
              itemMetadata.value = [generateTreeviewData(body.all).data];
            }
          });
        }
      },
      (error) => {
        itemGeneralInfo.value = {
          Error: "A network error occured while fetching metadata",
        };
        console.error(error);
      },
    );
  }
}

function closeDetails() {
  isViewingDetails.value = false;
}

function openContextMenu(e, file) {
  rightClickedItem.value = file;

  if (!selectedItems.value.includes(file)) {
    clearSelection();
    toggleFileSelected(file);
  }

  console.log(e.clientX, e.clientY);

  menuLocation.value = {
    x: e.clientX,
    y: e.clientY,
  };

  isRightClickMenuOpen.value = true;
}

function resetPreview(keepLoading = false) {
  if (imagePreviewUrl.value !== null) {
    URL.revokeObjectURL(imagePreviewUrl.value);
    imagePreviewUrl.value = null;
  }
  textPreview.value = null;
  codePreview.value = null;
  isLoadingPreview.value = keepLoading;
}

function getPreview(file) {
  resetPreview(true);
  fetch(
    "/preview/" +
      currentPath.value +
      file.name +
      "?" +
      new URLSearchParams({ page: "0" }),
    {
      method: "GET",
    },
  ).then(
    (response) => {
      response.blob().then(async (blob) => {
        console.log(blob.type);
        if (blob.type.includes("image/jpeg")) {
          imagePreviewUrl.value = URL.createObjectURL(blob);
        } else if (blob.type.includes("text/plain")) {
          const originalFileExtension = response.headers.get(
            "X-Original-File-Extension",
          );
          ((textPreview.value = await blob.text()),
            { language: originalFileExtension });
          if (originalFileExtension !== null) {
            codePreview.value = textPreview.value;
            textPreview.value = null;
            codePreviewLanguage.value = originalFileExtension;
          }
        }
        isLoadingPreview.value = false;
      });
    },
    (error) => {
      console.error("Encountered error while getting preview:", error);
      isLoadingPreview.value = false;
    },
  );
}

function createNewFolder() {
  fetch("/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      mode: "newFolder",
    },
    body: JSON.stringify({ path: currentPath.value }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("There was an error while creating a new folder.");
      }
      return response.json();
    })
    .then((response) => {
      updateItems().then((_) => {
        selectedItems.value = [
          sortedItems.value[
            sortedItems.value.findIndex((f) => f.name === response.name)
          ],
        ];
        promptNewName();
      });
    });
}

function createNewFile() {
  fetch("/modify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      mode: "newFile",
    },
    body: JSON.stringify({ path: currentPath.value }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("There was an error while creating a new file.");
      }
      return response.json();
    })
    .then((response) => {
      updateItems().then((_) => {
        selectedItems.value = [
          sortedItems.value[
            sortedItems.value.findIndex((f) => f.name === response.name)
          ],
        ];
        promptNewName();
      });
    });
}

function promptShare() {
  isSharing.value = true;
  generatedLink.value = "";
}

function isExpirationTimeCorrect(_ = 0) {
  return !(
    expirationTime.value === -1 &&
    customExpirationTimeDays.value === 0 &&
    customExpirationTimeHours.value === 0 &&
    customExpirationTimeMinutes.value === 0
  );
}

function generateLink() {
  isGeneratingLink.value = true;
  const actualExpirationTime =
    expirationTime.value !== -1
      ? expirationTime.value
      : customExpirationTimeDays.value * 86400 +
        customExpirationTimeHours.value * 3600 +
        customExpirationTimeMinutes.value * 60;
  fetch("/share/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      path: currentPath.value + selectedItems.value[0].name,
      expirationTime: actualExpirationTime,
    }),
  })
    .then((response) => {
      isGeneratingLink.value = false;
      if (!response.ok) {
        throw new Error(
          "There was an error while getting link for shared item.",
        );
      }
      return response.json();
    })
    .then((response) => {
      generatedLink.value = "bodi.homelinuxserver.org/shared/" + response;
    });
}

function copyLink() {
  navigator.clipboard.writeText(generatedLink.value).then((result) => {
    linkCopied.value = true;
  });
}

function search(query) {
  if (query.length === 0) {
    sortingMode.value = SortingModes.Name;
    updateItems();
    return;
  }

  const fuse = new Fuse(items.value, { keys: ["name"] });
  sortedItems.value = [];
  for (const result of fuse.search(query)) {
    sortedItems.value.push(result.item);
  }
  sortingMode.value = SortingModes.Search;
}

function isDialogOpen() {
  return (
    isRenaming.value ||
    isDeleting.value ||
    isSharing.value ||
    isViewingDetails.value
  );
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
  if (isSharing.value) {
    isSharing.value = false;
  }
}

const navigationDrawerMenus = [
  { text: "My Files", icon: "mdi-folder", page: Pages.MyFiles },
  { text: "Recent", icon: "mdi-history", page: Pages.Recent },
  { text: "Backups", icon: "mdi-cloud-upload", page: Pages.Backups },
  {
    text: "Jellyfin",
    icon: "mdi-television",
    href: "http://192.168.0.115:8096/",
  },
  {
    text: "qBittorrent",
    icon: "mdi-download",
    href: "http://192.168.0.115:8090/",
  },
];

const fileSizeUnits = {
  B: 1,
  KB: 1_000,
  MB: 1_000_000,
  GB: 1_000_000_000,
  TB: 1_000_000_000_000,
  PB: 1_000_000_000_000_000,
};

function areItemsSame(a, b) {
  return (
    a.name === b.name && a.size === b.size && a.lastModified === b.lastModified
  );
}

function getFileSizeDescription(fileSize) {
  if (fileSize < 0) {
    return "";
  }

  for (const [unit, size] of Object.entries(fileSizeUnits)) {
    let displayedSize = fileSize / size;
    if (displayedSize < 1_000) {
      return parseFloat(displayedSize.toFixed(2)).toString() + " " + unit;
    }
  }
}

function getItemLastModifiedDate(file) {
  const date = new Date(file.lastModified * 1000);

  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");

  return `${year}\u202F/\u202F${month}\u202F/\u202F${day} \u202F${hour}:${minute}`;
}

function getItemNameExtension(fileName) {
  let i = fileName.lastIndexOf(".");
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
  } else {
    return "File";
  }
}

function getItemSizeDescription(item) {
  const size = item.size > 0 ? item.size : directoryDetails.value.size;
  return size >= 0
    ? `${getFileSizeDescription(size)} (${size} bytes)`
    : "Loading...";
}

function changePath(file) {
  if (file.size === -1) {
    currentPath.value += file.name + "/";
    updateItems();
  } else {
    openFile(file);
  }
}

async function focusedPathEditField() {
  editedPath.value = currentPath.value;
  isEditingPath.value = true;

  await nextTick();

  const input = pathField.value?.$el?.querySelector('input')
  input?.select()
}

function setEditedPath() {
  if (editedPath.value.length !== 0 && editedPath.value.charAt(editedPath.value.length - 1) !== '/') {
      setCurrentPath(editedPath.value + '/');
    }
    else {
      if (editedPath.value !== currentPath.value) {
        setCurrentPath(editedPath.value);
      }
    }
  isEditingPath.value = false;
}

function getItemBorderRadius(file) {
  if (selectedItems.value.findIndex((f) => areItemsSame(f, file)) === -1) {
    return "25px 25px 25px 25px";
  }

  let i = sortedItems.value.findIndex((f) => areItemsSame(f, file));
  let doRoundTop =
    i !== 0
      ? selectedItems.value.findIndex((f) =>
          areItemsSame(f, sortedItems.value[i - 1]),
        ) === -1
      : true;
  let doRoundBottom =
    i !== sortedItems.value.length - 1
      ? selectedItems.value.findIndex((f) =>
          areItemsSame(f, sortedItems.value[i + 1]),
        ) === -1
      : true;

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

function getPathSubPaths() {
  let parts = [];
  let p = currentPath.value;
  while (p !== "") {
    parts.unshift(p);
    p = p.slice(0, p.lastIndexOf("/", p.length - 2) + 1);
  }
  return parts;
}

function getPathLastFolder(path) {
  return path.slice(
    path.lastIndexOf("/", path.length - 2) + 1,
    path.length - 1,
  );
}

function getPathParent(path) {
  const lastSlashIndex = path.lastIndexOf("/");
  if (lastSlashIndex !== -1) {
    return path.slice(0, lastSlashIndex);
  }
  return "";
}

function setCurrentPath(path) {
  currentPath.value = path;
  updateItems();
}

function goBackDirectory() {
  const pathParts = getPathSubPaths();
  if (pathParts.length === 1) {
    setCurrentPath("");
  } else {
    setCurrentPath(pathParts[pathParts.length - 2]);
  }
}

function signOut() {
  window.location.pathname = "/logout";
}

function handleNavigationDrawerClick(item) {
  if (item.page !== undefined) {
    currentPage.value = item.page;
  } else {
    window.location.href = item.href;
  }
}

function setSyntaxHighlightingTheme(theme) {
  console.log("Setting highlight theme to", theme);
  const link = document.getElementById("hljs-theme");
  link.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/${theme}.min.css`;
  link.onload = () => {
    codePreviewHighlightKey.value++;
    console.log("Loaded", theme);
  }
}

</script>

<script>
export default {
  configureWebpack: {
    devtool: "source-map",
  },
};
</script>

<style>
/* Base behavior (not styles) */
.preview-box {
  flex: 1;
  align-self: flex-start;
  min-width: 0;
  /* required for flex shrink */
  overflow: auto;
  /* ensures nice collapse */
  border: solid 1px rgba(var(--v-border-color), var(--v-border-opacity));
  /* you can Tailwind this too if you want */
  max-width: 100%;
  max-height: 100vh;
  /* or 100%, or clamp(), or via CSS var */
}

/* Transition animation */
.expand-x-enter-active,
.expand-x-leave-active {
  transition:
    max-width 0.5s ease-in-out,
    opacity 0.5s ease-in-out;
}

.expand-x-enter-from,
.expand-x-leave-to {
  max-width: 0;
  opacity: 0;
}

.expand-x-enter-to,
.expand-x-leave-from {
  max-width: 100%;
  /* match preview-box max-width */
  opacity: 1;
}

.no-underline .v-field__outline,
.no-underline .v-field__underlined::before,
.no-underline .v-field__underlined::after {
  display: none !important;
}

.no-text-field-data-padding .v-field__input {
  padding: 0;
  padding-left: 6px;
  overflow-x: auto;
}

.input-ml-6 .v-field__input {
  margin-left: 6px;
}
</style>