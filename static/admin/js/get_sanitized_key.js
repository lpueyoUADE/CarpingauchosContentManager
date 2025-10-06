const generatedNewSanitizedKey = new CustomEvent("generatedNewSanitizedKey");

function getSanitizedKey(input, modelName, fields, callback, doDispatchEvent=true) {
    /*
        modelname: referencia en backend para usar el keygenerator adecuado.
        fields: json de nombre de campo y su valor obtenido del front (inputs usualmente).
        input: input donde se actualiza la key obtenida.
    */
    // Convertimos el objeto en query string
    const params = new URLSearchParams(fields).toString();

    url = `/content/generate_key/${modelName}/?${params}`;

    fetch(url)
        .then(r => r.json())
        .then(data => {    
            callback?.(data.key);
            if(doDispatchEvent)
            {
                input.value = data.key;
                document.dispatchEvent(generatedNewSanitizedKey);
            }
        });
}