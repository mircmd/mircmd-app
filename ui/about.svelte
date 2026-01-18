<script lang="ts">
  import AppLogo from "./assets/app.png";
  import LICENSE from "./assets/LICENSE.txt?raw";
  import Tabs from "./lib/tabs.svelte";

  const tabs = [
    { id: "about", title: "About" },
    { id: "authors", title: "Authors" },
    { id: "license", title: "License" },
  ];
</script>

<main>
  <div class="header">
    <div>
      <img src={AppLogo} class="logo" alt="Mir Commander Logo" />
    </div>
    <div class="name disable-selection">Mir Commander</div>
    <div class="version disable-selection">Version {__APP_VERSION__}</div>
  </div>
  <div class="tab-container">
    <Tabs {tabs} activeTabId="about">
      {#snippet children(activeTabId)}
        {#if activeTabId === "about"}
          <div class="about-content">
            <p>
              A modern, powerful graphical user interface for molecular
              structure modeling.
            </p>
            <div class="contact-links">
              <span>Home Page:</span>
              <a href="https://mircmd.com/">https://mircmd.com/</a>
              <span>Telegram:</span>
              <a href="https://t.me/mir_commander">https://t.me/mir_commander</a
              >
            </div>
          </div>
        {:else if activeTabId === "authors"}
          <div class="authors">
            <div class="author">
              <p>Yury V. Vishnevskiy</p>
              <a href="mailto:yu.v.vishnevskiy@gmail.com"
                >yu.v.vishnevskiy@gmail.com</a
              >
            </div>
            <div class="author">
              <p>Valery V. Vishnevskiy</p>
              <a href="mailto:v.v.vishnevskiy@gmail.com"
                >v.v.vishnevskiy@gmail.com</a
              >
            </div>
          </div>
        {:else if activeTabId === "license"}
          <div class="license">
            <pre>{LICENSE}</pre>
          </div>
        {/if}
      {/snippet}
    </Tabs>
  </div>
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    padding: 12px;
    box-sizing: border-box;
  }

  .header {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .tab-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    width: 100%;
    min-height: 0;
  }

  .logo {
    height: 50px;
    width: 50px;
  }

  .name {
    font-size: 15.5px;
    font-weight: bold;
    margin-top: 10px;
  }

  .version {
    font-size: 10.7px;
    margin-top: 7px;
    margin-bottom: 7px;
  }

  .about-content {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    height: 100%;
    padding: 10px;
    box-sizing: border-box;
  }

  .about-content p {
    margin: 0 0 10px 0;
  }

  .contact-links {
    display: inline-grid;
    grid-template-columns: auto auto;
    gap: 5px 10px;
    align-items: center;
    justify-self: start;
  }

  .contact-links a {
    justify-self: start;
  }

  .authors {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 20px;
  }

  .author {
    text-align: center;
  }

  .author p {
    margin: 0 0 5px 0;
  }

  .license {
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: white;
    padding: 4px;
    box-sizing: border-box;
    border-left: 1px solid #dadada;
    border-right: 1px solid #dadada;
    border-bottom: 1px solid #dadada;
  }

  .license pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 11.9px;
  }
</style>
