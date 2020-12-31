window.getEdjs = function getEdjs(holdname, data, readonly) {
	const editor = new EditorJS({
  holder: holdname,
  tools: {
    header: {
      class: Header,
      inlineToolbar : true,
      config: {
        placeholder: 'Введите заголовок',
        levels: [2, 3, 4],
        defaultLevel: 3
      },
    
    },
    simage: SimpleImage,
    image: {
      class: ImageTool,
      config: {
        endpoints: {
          byFile: 'http://localhost:8008/uploadFile', // Your backend file uploader endpoint
          byUrl: 'http://localhost:8008/fetchUrl', // Your endpoint that provides uploading by Url
        }
      }
    },
    linkTool: {
      class: LinkTool,
      inlineToolbar : true,
      config: {
        endpoint: 'http://localhost:8008/fetchUrl', // Your backend endpoint for url data fetching
      }
    },
    checklist: {
      class: Checklist,
      inlineToolbar: true,
    },
    list: {
      class: List,
      inlineToolbar: true,
    },
    embed: {
      class: Embed,
      inlineToolbar: true,
    },
  },

  readOnly: readonly,

  /**
   * Previously saved data that should be rendered
   */
  data: data
});
	return editor;


}
